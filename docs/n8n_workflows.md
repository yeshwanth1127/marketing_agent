# n8n Workflow Documentation

This document describes the n8n workflows for data ingestion from Meta Ads and GA4 APIs.

## Overview

n8n workflows are responsible for:
- Scheduled data pulls from marketing platforms
- OAuth token management and refresh
- API pagination handling
- Rate limit management
- Data normalization
- Database writes (upserts)

## Prerequisites

1. **n8n Instance**: Self-hosted or cloud n8n instance
2. **API Credentials**:
   - Meta Ads API: App ID, App Secret, Access Token
   - GA4 API: Service Account JSON key
3. **Database Access**: PostgreSQL connection string
4. **API Endpoint**: Marketing Intelligence Pipeline API endpoint (for triggering agent runs)

---

## Workflow 1: Meta Ads Data Ingestion

**Schedule**: Daily at 2:00 AM  
**Purpose**: Pull campaign insights from Meta Ads API and store in PostgreSQL

### Workflow Steps

#### 1. Cron Trigger
- **Node Type**: Cron
- **Schedule**: `0 2 * * *` (Daily at 2:00 AM)
- **Timezone**: Your timezone

#### 2. Get Access Token (OAuth Refresh)
- **Node Type**: HTTP Request
- **Method**: POST
- **URL**: `https://graph.facebook.com/v18.0/oauth/access_token`
- **Body Parameters**:
  ```
  grant_type: long_lived_access_token
  client_id: {{ $env.META_ADS_APP_ID }}
  client_secret: {{ $env.META_ADS_APP_SECRET }}
  access_token: {{ $env.META_ADS_ACCESS_TOKEN }}
  ```
- **Response**: Extract `access_token` from response

#### 3. Get All Campaigns
- **Node Type**: HTTP Request
- **Method**: GET
- **URL**: `https://graph.facebook.com/v18.0/{{ $env.META_ADS_ACCOUNT_ID }}/campaigns`
- **Headers**:
  ```
  Authorization: Bearer {{ $node["Get Access Token"].json["access_token"] }}
  ```
- **Query Parameters**:
  ```
  fields: id,name,status
  limit: 100
  ```
- **Pagination**: Enable "Paginate" option for automatic pagination

#### 4. For Each Campaign (Loop)
- **Node Type**: Split In Batches
- **Batch Size**: 1 (process one campaign at a time)
- **OR** use "HTTP Request" node with "Execute Once for Each Item" enabled

#### 5. Get Campaign Insights
- **Node Type**: HTTP Request
- **Method**: GET
- **URL**: `https://graph.facebook.com/v18.0/{{ $json["id"] }}/insights`
- **Headers**:
  ```
  Authorization: Bearer {{ $node["Get Access Token"].json["access_token"] }}
  ```
- **Query Parameters**:
  ```
  fields: impressions,clicks,spend,actions,action_values
  date_preset: last_7d
  level: campaign
  time_increment: 1
  ```
- **Note**: Adjust `date_preset` or use `time_range` for specific date ranges

#### 6. Transform Data (Normalize)
- **Node Type**: Code (JavaScript)
- **Purpose**: Transform Meta Ads format to canonical format
- **Code**:
  ```javascript
  const items = $input.all();
  const normalized = [];

  for (const item of items) {
    const insight = item.json;
    const date = insight.date_start || insight.date_stop;
    
    // Extract conversions (purchases)
    const actions = insight.actions || [];
    const purchaseAction = actions.find(a => a.action_type === 'purchase') || {};
    const conversions = parseInt(purchaseAction.value || 0);
    
    // Extract revenue (purchase value)
    const actionValues = insight.action_values || [];
    const purchaseValue = actionValues.find(a => a.action_type === 'purchase') || {};
    const revenue = parseFloat(purchaseValue.value || 0);

    normalized.push({
      json: {
        external_id: item.json.campaign_id || item.json.id,
        campaign_name: item.json.campaign_name || item.json.campaign_name,
        date: date,
        impressions: parseInt(insight.impressions || 0),
        clicks: parseInt(insight.clicks || 0),
        spend: parseFloat(insight.spend || 0),
        conversions: conversions,
        revenue: revenue,
        source: "meta_ads",
        status: item.json.campaign_status || "active"
      }
    });
  }

  return normalized;
  ```

#### 7. Upsert to Database (HTTP Request to API)
- **Node Type**: HTTP Request
- **Method**: POST
- **URL**: `{{ $env.API_BASE_URL }}/api/ingestion/upsert`
- **Body**:
  ```json
  {
    "raw_data": {{ $json }},
    "source": "meta_ads"
  }
  ```
- **Headers**:
  ```
  Content-Type: application/json
  ```

#### 8. Error Handling
- **Node Type**: Error Trigger
- **Actions**: Log errors, send notifications, retry logic

#### 9. Log Completion
- **Node Type**: HTTP Request (or Slack/Email)
- **Purpose**: Log successful completion

### Environment Variables

```bash
META_ADS_APP_ID=your_app_id
META_ADS_APP_SECRET=your_app_secret
META_ADS_ACCESS_TOKEN=your_access_token
META_ADS_ACCOUNT_ID=your_account_id
API_BASE_URL=http://localhost:8000
```

---

## Workflow 2: GA4 Data Ingestion

**Schedule**: Daily at 3:00 AM  
**Purpose**: Pull traffic and conversion data from GA4 API and store in PostgreSQL

### Workflow Steps

#### 1. Cron Trigger
- **Node Type**: Cron
- **Schedule**: `0 3 * * *` (Daily at 3:00 AM)
- **Timezone**: Your timezone

#### 2. Authenticate GA4 API
- **Node Type**: Code (JavaScript) or HTTP Request
- **Purpose**: Generate OAuth2 access token from service account
- **Note**: Use GA4 Data API service account authentication
- **Code Example**:
  ```javascript
  // Use Google Auth library or HTTP request to get access token
  // For service account, use JWT-based authentication
  ```

#### 3. Get Report Data
- **Node Type**: HTTP Request
- **Method**: POST
- **URL**: `https://analyticsdata.googleapis.com/v1beta/properties/{{ $env.GA4_PROPERTY_ID }}:runReport`
- **Headers**:
  ```
  Authorization: Bearer {{ $node["Authenticate GA4 API"].json["access_token"] }}
  Content-Type: application/json
  ```
- **Body**:
  ```json
  {
    "dateRanges": [
      {
        "startDate": "7daysAgo",
        "endDate": "yesterday"
      }
    ],
    "dimensions": [
      {"name": "date"},
      {"name": "sourceMedium"}
    ],
    "metrics": [
      {"name": "sessions"},
      {"name": "totalUsers"},
      {"name": "purchases"},
      {"name": "purchaseRevenue"}
    ]
  }
  ```

#### 4. Transform Data (Normalize)
- **Node Type**: Code (JavaScript)
- **Purpose**: Transform GA4 format to canonical format
- **Code**:
  ```javascript
  const items = $input.all();
  const normalized = [];

  for (const item of items) {
    const row = item.json;
    const dimensionValues = row.dimensionValues || [];
    const metricValues = row.metricValues || [];

    const date = dimensionValues[0]?.value || "";
    const sourceMedium = dimensionValues[1]?.value || "unknown";
    const sessions = parseInt(metricValues[0]?.value || 0);
    const purchases = parseInt(metricValues[2]?.value || 0);
    const revenue = parseFloat(metricValues[3]?.value || 0);

    // Format date from YYYYMMDD to YYYY-MM-DD
    const formattedDate = `${date.substring(0, 4)}-${date.substring(4, 6)}-${date.substring(6, 8)}`;

    normalized.push({
      json: {
        external_id: `ga4_${sourceMedium.replace(/\s+/g, '_')}`,
        campaign_name: sourceMedium,
        date_start: formattedDate,
        impressions: sessions * 2, // Estimate
        clicks: sessions,
        cost: 0, // GA4 doesn't provide cost, set to 0 or fetch from Google Ads
        purchases: purchases,
        value: revenue,
        source: "ga4",
        status: "active"
      }
    });
  }

  return normalized;
  ```

#### 5. Upsert to Database (HTTP Request to API)
- **Node Type**: HTTP Request
- **Method**: POST
- **URL**: `{{ $env.API_BASE_URL }}/api/ingestion/upsert`
- **Body**:
  ```json
  {
    "raw_data": {{ $json }},
    "source": "ga4"
  }
  ```
- **Headers**:
  ```
  Content-Type: application/json
  ```

#### 6. Error Handling
- **Node Type**: Error Trigger
- **Actions**: Log errors, send notifications, retry logic

#### 7. Log Completion
- **Node Type**: HTTP Request (or Slack/Email)
- **Purpose**: Log successful completion

### Environment Variables

```bash
GA4_PROPERTY_ID=your_property_id
GA4_SERVICE_ACCOUNT_KEY=path_to_service_account_json
API_BASE_URL=http://localhost:8000
```

---

## Workflow 3: Trigger Weekly Agent Run

**Schedule**: Weekly on Monday at 9:00 AM  
**Purpose**: Trigger the weekly agent analysis after data ingestion

### Workflow Steps

#### 1. Cron Trigger
- **Node Type**: Cron
- **Schedule**: `0 9 * * 1` (Every Monday at 9:00 AM)

#### 2. Trigger Agent Run
- **Node Type**: HTTP Request
- **Method**: POST
- **URL**: `{{ $env.API_BASE_URL }}/api/agent/run-weekly`
- **Headers**:
  ```
  Content-Type: application/json
  ```
- **Body**:
  ```json
  {
    "date_range_days": 30
  }
  ```

#### 3. Handle Response
- **Node Type**: Code (JavaScript)
- **Purpose**: Format response and send to Slack/Dashboard

---

## API Endpoint: Data Ingestion

You'll need to create an API endpoint in the FastAPI app to handle upserts from n8n:

### Endpoint: `POST /api/ingestion/upsert`

**Request Body**:
```json
{
  "raw_data": {
    "external_id": "meta_ads_123456",
    "campaign": "Campaign Name",
    "date": "2024-01-08",
    "impressions": 50000,
    "clicks": 340,
    "spend": 1200.00,
    "conversions": 12,
    "revenue": 9000.00
  },
  "source": "meta_ads"
}
```

**Response**:
```json
{
  "success": true,
  "campaign_id": "uuid",
  "metric_id": "uuid"
}
```

---

## Error Handling & Retries

### Retry Logic
- Configure retry in n8n HTTP Request nodes
- Max retries: 3
- Retry delay: Exponential backoff (1s, 2s, 4s)

### Error Notifications
- Send errors to Slack/Email
- Log errors to monitoring system
- Alert on repeated failures

### Data Validation
- Validate data before database writes
- Log validation errors
- Skip invalid records (don't fail entire batch)

---

## Best Practices

1. **Rate Limiting**: Respect API rate limits (use delays between requests)
2. **Pagination**: Handle paginated responses properly
3. **Idempotency**: Use upserts to handle duplicate data
4. **Logging**: Log all API calls and errors
5. **Monitoring**: Monitor workflow execution and success rates
6. **Testing**: Test workflows with small data sets first
7. **Credentials**: Store credentials securely (use n8n credentials or environment variables)

---

## Troubleshooting

### Common Issues

1. **OAuth Token Expired**
   - Solution: Implement token refresh logic
   - Check token expiration time

2. **Rate Limit Exceeded**
   - Solution: Add delays between requests
   - Use batch processing

3. **Data Format Mismatch**
   - Solution: Check transformation code
   - Validate normalized data format

4. **Database Connection Errors**
   - Solution: Check database connection string
   - Verify database is accessible from n8n instance

---

## Next Steps

1. Set up n8n instance (self-hosted or cloud)
2. Configure API credentials
3. Create workflows using this documentation
4. Test with small data sets
5. Schedule workflows
6. Monitor execution and errors

