# Splunk Amazon Connect API Metrics Processor

Fetches **Amazon Connect** real-time and historical metrics from Connect REST endpoints and sends them to an **Amazon Kinesis Data Stream** for downstream ingestion into Splunk (for example, via Kinesis Data Firehose).

## Project overview

This serverless application consists of an **AWS Lambda** function that runs every minute and:

1. **Lists queues** in the Amazon Connect instance (`ListQueues`).
2. **Collects real-time metrics** per queue and aggregated (`GetCurrentMetricData`).
3. **Collects historical metrics** per queue and aggregated (`GetMetricData`).
4. **Collects v2 metrics** per queue, per agent, and general (`GetMetricDataV2`).
5. **Collects real-time user data** (`GetCurrentUserData`).
6. **Writes all records** to a Kinesis Data Stream via `PutRecords`.

Data in the stream can then be consumed by **Kinesis Data Firehose** to send it to **Splunk** (HEC) or any other destination.

### Simplified architecture

```
EventBridge (rate 1 min) → Lambda (MetricsProcessor)
                                ↓
                    Amazon Connect APIs (metrics)
                                ↓
                    Kinesis Data Stream
                                ↓
                    Kinesis Data Firehose (optional)
                                ↓
                    Splunk (HEC)
```

### Data types sent to the stream

| Source | Description |
|--------|-------------|
| **Real-time queue metrics** | Available/on-call agents, contacts in queue, oldest contact age, etc. |
| **Historical queue metrics** | Contacts handled/abandoned, queue time, wait time, service level, etc. |
| **Queue GetMetricDataV2** | Detailed queue metrics (15-minute intervals). |
| **Agent GetMetricDataV2** | Per-agent metrics (handle times, abandons, etc.). |
| **GetCurrentUserData** | Current user/agent state (queue, status, etc.). |
| **Aggregated metrics** | Real-time and historical totals without queue breakdown. |

---

## Prerequisites

- **AWS account** with permissions to create and modify resources (Lambda, Kinesis, IAM, CloudWatch Logs, Connect).
- **Amazon Connect instance** already created, with queues configured.
- **Python 3.8** (for local development/packaging; in AWS the Lambda uses the runtime defined in the template).
- **AWS SAM CLI** (recommended for deployment) or **AWS CLI** and **CloudFormation**.

### Get the Connect instance ID

In the Amazon Connect console: **Settings** → **Instance alias** → the **Instance ID** is a UUID (for example `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).

---

## Repository structure

```
.
├── README.md
├── LICENSE
├── template.yaml                 # SAM template (Lambda + EventBridge schedule)
├── MetricsProcessor/
│   ├── lambda_function.py        # Lambda code
│   └── requirements.txt         # Dependencies (boto3)
└── cloudformation/
    ├── kds-to-splunk-via-kdf.json       # Firehose from existing KDS → Splunk
    └── new-kds-to-splunk-via-kdf.json   # Creates KDS + Firehose → Splunk
```

---

## Installation and deployment

### 1. Clone the repository

```bash
git clone https://github.com/splunk/splunk-aws-connect-api-metrics-processor.git
cd splunk-aws-connect-api-metrics-processor
```

### 2. Create the Kinesis Data Stream (if it does not exist yet)

You can create the stream manually or use the `cloudformation/new-kds-to-splunk-via-kdf.json` template, which also configures Firehose to Splunk (see *Optional: send data to Splunk*).

To create only the stream from the AWS console:

- **Kinesis** → **Data streams** → **Create data stream**.
- Stream name (for example `connect-metrics-stream`).
- Shard count (for example 1 to start).

Write down the **stream name**; you will need it in the next step.

### 3. Deploy the SAM application (Lambda + schedule)

#### Option A: Using AWS SAM CLI

1. **Install SAM CLI** (if you do not have it yet):

   - [Guía de instalación AWS SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html).

2. **Build and deploy**:

   ```bash
   sam build
   sam deploy --guided
   ```

   During `--guided` you will be prompted for:

   - **Stack name**: for example `connect-metrics-processor`.
   - **AWS Region**: the same region where your Connect instance and Kinesis stream exist.
   - **Parameter ConnectInstanceId**: UUID of your Amazon Connect instance.
   - **Parameter KinesisStreamName**: Kinesis Data Stream name (e.g., `connect-metrics-stream`).
   - Confirmation for IAM permissions and role creation.

3. **Subsequent deployments** (without the wizard):

   ```bash
   sam build && sam deploy
   ```

#### Option B: From the AWS Serverless Application Repository

If the application is published in the [AWS Serverless Application Repository](https://serverlessrepo.aws.amazon.com/), you can deploy it from the console by providing:

- **ConnectInstanceId**: Connect instance ID.
- **KinesisStreamName**: Kinesis stream name.

### 4. Verify the deployment

- In **Lambda**: a function (for example `MetricsProcessor`) should exist with a scheduled event **rate(1 minute)**.
- In **CloudWatch Logs**: a log group for that function should exist; after 1–2 minutes you should see successful executions.
- In **Kinesis**: in your stream’s **Monitoring** tab, you should see incoming records every minute.

---

## SAM template parameters

| Parameter | Type | Description |
|----------|------|-------------|
| **ConnectInstanceId** | String | UUID of the Amazon Connect instance. |
| **KinesisStreamName** | String | Name of the Kinesis Data Stream where metrics are written. |

---

## Lambda IAM permissions

The function uses a policy that allows:

- **CloudWatch Logs**: create log group/stream and write logs.
- **Amazon Connect**: `ListQueues`, `DescribeInstance`, `GetCurrentMetricData`, `GetMetricData`, `GetMetricDataV2`, `GetCurrentUserData` for the instance.
- **Kinesis**: `PutRecords` only to the stream specified by `KinesisStreamName`.

Ensure your Connect instance and Kinesis stream are in the same account and region as the Lambda, or adjust ARNs in the template as needed.

---

## Optional: send data to Splunk

To forward data from the Kinesis Data Stream to Splunk, you can use **Kinesis Data Firehose** with a Splunk (HEC) destination.

If your goal is dashboards and analysis for Amazon Connect data in Splunk, you may also want to install the [Splunk App for Amazon Connect (Splunkbase)](https://splunkbase.splunk.com/app/5206) once data is flowing into your Splunk platform.

There are two templates under `cloudformation/`:

1. **`kds-to-splunk-via-kdf.json`**  
   - Assumes the **Kinesis Data Stream already exists** (the one used by the Lambda).  
   - Creates the Firehose role, the Delivery Stream (source = your KDS), and the Splunk (HEC) destination configuration.  
   - Parameters: `KinesisStreamName`, `SplunkHECEndpoint`, `SplunkHECToken`.

2. **`new-kds-to-splunk-via-kdf.json`**  
   - **Creates** the Kinesis Data Stream, plus Firehose and the Splunk destination.  
   - Useful if you want to deploy everything at once.  
   - Parameters: same as above.

### Deploy Firehose to Splunk (existing stream)

1. From Splunk, obtain:
   - **HEC endpoint** (HTTP Event Collector URL).
   - **HEC token** (authentication token).

2. Create a CloudFormation stack from `kds-to-splunk-via-kdf.json`:

   ```bash
   aws cloudformation create-stack \
     --stack-name connect-metrics-to-splunk \
     --template-body file://cloudformation/kds-to-splunk-via-kdf.json \
     --parameters \
       ParameterKey=KinesisStreamName,ParameterValue=connect-metrics-stream \
       ParameterKey=SplunkHECEndpoint,ParameterValue=https://splunk.example.com:8088/services/collector \
       ParameterKey=SplunkHECToken,ParameterValue=YOUR_HEC_TOKEN
   ```

   Replace the stream name, HEC URL, and token with your own values.

3. After deployment, Firehose will read from the same stream where the Lambda writes and will forward events to Splunk.

---

## Configuration and environment

The Lambda reads two environment variables (set by the SAM template):

| Variable | Source | Description |
|----------|--------|-------------|
| **CONNECT_INSTANCE_ID** | `ConnectInstanceId` parameter | Connect instance ID. |
| **KINESIS_STREAM_NAME** | `KinesisStreamName` parameter | Kinesis stream name. |

You do not need to configure credentials; the function uses the IAM role assigned by SAM/CloudFormation.

---

## Frequency and time windows

- **Execution**: every **1 minute** (configured in `template.yaml` as `rate(1 minute)`).
- **Historical metrics**: last-hour window, aligned to 5-minute boundaries.
- **GetMetricDataV2**: 15-minute interval (`FIFTEEN_MIN`).

---

## Local development (optional)

```bash
cd MetricsProcessor
pip install -r requirements.txt
```

The handler is `lambda_function.lambda_handler`. For local testing you can use [SAM local invoke](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-local-invoke.html) or run a script that simulates the event and environment variables.

---

## Further reading

- [Levelling up your Amazon Connect with Splunk (PDF)](https://www.splunk.com/en_us/pdfs/resources/whitepaper/levelling-up-your-amazon-connect-with-splunk.pdf) — An end-to-end guide that covers common Amazon Connect ingest points and Splunk-side setup patterns.

---

## License

MIT License. See [LICENSE](LICENSE).

---

## References

- [Amazon Connect API Reference](https://docs.aws.amazon.com/connect/latest/APIReference/)
- [GetCurrentMetricData](https://docs.aws.amazon.com/connect/latest/APIReference/API_GetCurrentMetricData.html)
- [GetMetricData / GetMetricDataV2](https://docs.aws.amazon.com/connect/latest/APIReference/API_GetMetricDataV2.html)
- [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/)
- [Kinesis Data Firehose – Splunk destination](https://docs.aws.amazon.com/firehose/latest/dev/destinations-splunk.html)
