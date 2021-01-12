import os
import boto3
import datetime
import json

# The splunk-aws-connect-api-metrics-processor program retrieves connect metrics from two endpoints (getMetricData and getCurrentMetricData) for real-time and historical data.
# The endpoints are queried twice once for queue specific metrics and again for aggregated queue metrics.
# The results are then sent to be stored in a Kinesis Stream.

# https://docs.aws.amazon.com/connect/latest/APIReference/API_ListQueues.html
def get_queues(client, instance_id):
	queues = []
	response = client.list_queues(InstanceId=instance_id)
	queue_summary_list = response['QueueSummaryList']
	for row in queue_summary_list:
		if row['QueueType'] == 'STANDARD':
			queues.append({
				"Name": row['Name'],
				"Id": row['Id'],
				"Arn": row['Arn'],
			})

	return queues


# https://docs.aws.amazon.com/connect/latest/APIReference/API_GetMetricData.html
def get_historic_metric_data(client, instance_id, queues, start_time, end_time, group=None):
	groupings = []
	if group:
		groupings.append(group)

	queues_list = []
	for queue in queues:
		queues_list.append(queue['Id'])

	response = client.get_metric_data(
		InstanceId=instance_id,
		Filters={'Queues': queues_list, 'Channels': ["VOICE"]},
		Groupings=groupings,
		StartTime=start_time,
		EndTime=end_time,
		HistoricalMetrics=[
			{
				"Name": "ABANDON_TIME",
				"Unit": "SECONDS",
				"Statistic": "AVG"
			},
			{
				"Name": "AFTER_CONTACT_WORK_TIME",
				"Unit": "SECONDS",
				"Statistic": "AVG"
			},
			{
				"Name": "API_CONTACTS_HANDLED",
				"Unit": "COUNT",
				"Statistic": "SUM"
			},
			{
				"Name": "CALLBACK_CONTACTS_HANDLED",
				"Unit": "COUNT",
				"Statistic": "SUM"
			},
			{
				"Name": "CONTACTS_ABANDONED",
				"Unit": "COUNT",
				"Statistic": "SUM"
			},
			{
				"Name": "CONTACTS_AGENT_HUNG_UP_FIRST",
				"Unit": "COUNT",
				"Statistic": "SUM"
			},
			{
				"Name": "CONTACTS_CONSULTED",
				"Unit": "COUNT",
				"Statistic": "SUM"
			},
			{
				"Name": "CONTACTS_CONSULTED",
				"Unit": "COUNT",
				"Statistic": "SUM"
			},
			{
				"Name": "CONTACTS_HANDLED",
				"Unit": "COUNT",
				"Statistic": "SUM"
			},
			{
				"Name": "CONTACTS_HANDLED_INCOMING",
				"Unit": "COUNT",
				"Statistic": "SUM"
			},
			{
				"Name": "CONTACTS_HANDLED_OUTBOUND",
				"Unit": "COUNT",
				"Statistic": "SUM"
			},
			{
				"Name": "CONTACTS_HOLD_ABANDONS",
				"Unit": "COUNT",
				"Statistic": "SUM"
			},
			{
				"Name": "CONTACTS_MISSED",
				"Unit": "COUNT",
				"Statistic": "SUM"
			},
			{
				"Name": "CONTACTS_QUEUED",
				"Unit": "COUNT",
				"Statistic": "SUM"
			},
			{
				"Name": "CONTACTS_TRANSFERRED_IN",
				"Unit": "COUNT",
				"Statistic": "SUM"
			},
			{
				"Name": "CONTACTS_TRANSFERRED_IN_FROM_QUEUE",
				"Unit": "COUNT",
				"Statistic": "SUM"
			},
			{
				"Name": "CONTACTS_TRANSFERRED_OUT_FROM_QUEUE",
				"Unit": "COUNT",
				"Statistic": "SUM"
			},
			{
				"Name": "HANDLE_TIME",
				"Unit": "SECONDS",
				"Statistic": "AVG"
			},
			{
				"Name": "HOLD_TIME",
				"Unit": "SECONDS",
				"Statistic": "AVG"
			},
			{
				"Name": "INTERACTION_AND_HOLD_TIME",
				"Unit": "SECONDS",
				"Statistic": "AVG"
			},
			{
				"Name": "INTERACTION_TIME",
				"Unit": "SECONDS",
				"Statistic": "AVG"
			},
			{
				"Name": "OCCUPANCY",
				"Unit": "PERCENT",
				"Statistic": "AVG"
			},
			{
				"Name": "QUEUE_ANSWER_TIME",
				"Unit": "SECONDS",
				"Statistic": "AVG"
			},
			{
				"Name": "QUEUED_TIME",
				"Unit": "SECONDS",
				"Statistic": "MAX"
			},
			{
				"Name": "SERVICE_LEVEL",
				"Threshold": {
					"Comparison": "LT",
					"ThresholdValue": 15.0
				},
				"Unit": "PERCENT",
				"Statistic": "AVG"
			},
			{
				"Name": "SERVICE_LEVEL",
				"Threshold": {
					"Comparison": "LT",
					"ThresholdValue": 30.0
				},
				"Unit": "PERCENT",
				"Statistic": "AVG"
			},
			{
				"Name": "SERVICE_LEVEL",
				"Threshold": {
					"Comparison": "LT",
					"ThresholdValue": 60.0
				},
				"Unit": "PERCENT",
				"Statistic": "AVG"
			}
		]
	)
	return response


# https://docs.aws.amazon.com/connect/latest/APIReference/API_GetCurrentMetricData.html
def get_current_metric_data(client, instance_id, queues, group=None):
	groupings = []
	if group:
		groupings.append(group)

	queues_list = []
	for queue in queues:
		queues_list.append(queue['Id'])

	response = client.get_current_metric_data(
		InstanceId=instance_id,
		Filters={'Queues': queues_list, 'Channels': ["VOICE"]},
		Groupings=groupings,
		CurrentMetrics=[
			{
				"Name": "AGENTS_AFTER_CONTACT_WORK",
				"Unit": "COUNT"
			},
			{
				"Name": "AGENTS_AVAILABLE",
				"Unit": "COUNT"
			},
			{
				"Name": "AGENTS_ERROR",
				"Unit": "COUNT"
			},
			{
				"Name": "AGENTS_NON_PRODUCTIVE",
				"Unit": "COUNT"
			},
			{
				"Name": "AGENTS_ON_CALL",
				"Unit": "COUNT"
			},
			{
				"Name": "AGENTS_ON_CONTACT",
				"Unit": "COUNT"
			},
			{
				"Name": "AGENTS_ONLINE",
				"Unit": "COUNT"
			},
			{
				"Name": "AGENTS_STAFFED",
				"Unit": "COUNT"
			},
			{
				"Name": "CONTACTS_IN_QUEUE",
				"Unit": "COUNT"
			},
			{
				"Name": "CONTACTS_SCHEDULED",
				"Unit": "COUNT"
			},
			{
				"Name": "OLDEST_CONTACT_AGE",
				"Unit": "SECONDS"
			},
			{
				"Name": "SLOTS_ACTIVE",
				"Unit": "COUNT"
			},
			{
				"Name": "SLOTS_AVAILABLE",
				"Unit": "COUNT"
			},
		],
		MaxResults=100
	)
	return response


def lambda_handler(event, context):
	connect_client = boto3.client(service_name='connect')
	kinesis_client = boto3.client(service_name='kinesis')
	instance_id = os.environ['CONNECT_INSTANCE_ID']
	queues = get_queues(connect_client, instance_id)
	time_now = datetime.datetime.now()
	# Round to last 5 minutes for historical metrics
	end_time_rounded = datetime.datetime.now().replace(time_now.year, time_now.month, time_now.day, time_now.hour, (time_now.minute - (time_now.minute % 5)), 0, 0)
	start_time = end_time_rounded - datetime.timedelta(minutes=60)

	# All metric records
	all_metric_records_for_all_queues = []

	# Get metric records by queue
	real_time_metrics_by_queue = get_current_metric_data(connect_client, instance_id, queues, "QUEUE")
	historical_metrics_by_queue = get_historic_metric_data(connect_client, instance_id, queues, start_time, end_time_rounded, "QUEUE")
	metric_results_by_queue = real_time_metrics_by_queue['MetricResults'] + historical_metrics_by_queue['MetricResults']
	for r in metric_results_by_queue:
		for queue in queues:
			if r['Dimensions']['Queue']['Id'] == queue['Id']:
				r['Dimensions']['Queue']['Name'] = queue["Name"]

		metric_records_by_queue = {'Data': json.dumps(r).encode(), 'PartitionKey': r['Dimensions']['Queue']['Name']}
		all_metric_records_for_all_queues.append(metric_records_by_queue)

	# aggregated real time metrics
	agg_real_time_metrics_records = {}
	agg_real_time_metrics = get_current_metric_data(connect_client, instance_id, queues)
	if agg_real_time_metrics['MetricResults']:
		agg_real_time_metrics_records['Data'] = json.dumps(agg_real_time_metrics['MetricResults'][0]).encode()
		agg_real_time_metrics_records['PartitionKey'] = "Queue"
		all_metric_records_for_all_queues.append(agg_real_time_metrics_records)

	# aggregated historic metrics
	agg_historic_metrics_records = {}
	agg_historic_metrics = get_historic_metric_data(connect_client, instance_id, queues, start_time, end_time_rounded)
	if agg_historic_metrics['MetricResults']:
		agg_historic_metrics_records['Data'] = json.dumps(agg_historic_metrics['MetricResults'][0]).encode()
		agg_historic_metrics_records['PartitionKey'] = "Queue"
		all_metric_records_for_all_queues.append(agg_historic_metrics_records)

	kinesis_client.put_records(
		StreamName=os.environ['KINESIS_STREAM_NAME'],
		Records=all_metric_records_for_all_queues
	)
