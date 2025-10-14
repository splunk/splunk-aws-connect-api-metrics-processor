import os
import boto3
import datetime
import json
import logging

# The splunk-aws-connect-api-metrics-processor program retrieves connect metrics from two endpoints (getMetricData and getCurrentMetricData) for real-time and historical data.
# The endpoints are queried twice once for queue specific metrics and again for aggregated queue metrics.
# The results are then sent to be stored in a Kinesis Stream.

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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


#https://docs.aws.amazon.com/connect/latest/APIReference/API_GetMetricDataV2.html

def get_metric_data_v2(client, instance_arn, queues, start_time, end_time, grouping_type="GENERAL"):
    metrics = {
		"AGENT": [
			{"Name":"ABANDONMENT_RATE"},
			{"Name":"AGENT_ADHERENT_TIME"},
			{"Name":"AGENT_ANSWER_RATE"},
			{"Name":"AGENT_NON_ADHERENT_TIME"},
			{"Name":"AGENT_NON_RESPONSE"},
			{"Name":"AGENT_NON_RESPONSE_WITHOUT_CUSTOMER_ABANDONS"},
			{"Name":"AGENT_SCHEDULE_ADHERENCE"},
			{"Name":"AGENT_SCHEDULED_TIME"},
			{"Name":"AVG_ABANDON_TIME"},
			{"Name":"AVG_ACTIVE_TIME"},
			{"Name":"AVG_AFTER_CONTACT_WORK_TIME"},
			{"Name":"AVG_AGENT_PAUSE_TIME"},
			{"Name":"AVG_CONTACT_DURATION"},
			{"Name":"AVG_CONVERSATION_DURATION"},
			{"Name":"AVG_DIALS_PER_MINUTE"},
			{"Name":"AVG_EVALUATION_SCORE"},
			{"Name":"AVG_GREETING_TIME_AGENT"},
			{"Name":"AVG_HANDLE_TIME"},
			{"Name":"AVG_HOLD_TIME"},
			{"Name":"AVG_HOLD_TIME_ALL_CONTACTS"},
			{"Name":"AVG_HOLDS"},
			{"Name":"AVG_INTERACTION_AND_HOLD_TIME"},
			{"Name":"AVG_INTERACTION_TIME"},
			{"Name":"AVG_INTERRUPTIONS_AGENT"},
			{"Name":"AVG_INTERRUPTION_TIME_AGENT"},
			{"Name":"AVG_NON_TALK_TIME"},
			{"Name":"AVG_QUEUE_ANSWER_TIME"},
			{"Name":"AVG_RESOLUTION_TIME"},
			{"Name":"AVG_TALK_TIME"},
			{"Name":"AVG_TALK_TIME_AGENT"},
			{"Name":"AVG_TALK_TIME_CUSTOMER"},
			{"Name":"AVG_WEIGHTED_EVALUATION_SCORE"},
			{"Name":"CONTACTS_CREATED"},
			{"Name":"CONTACTS_HANDLED"},
			{"Name":"CONTACTS_HANDLED_BY_CONNECTED_TO_AGENT"},
			{"Name":"CONTACTS_HOLD_ABANDONS"},
			{"Name":"CONTACTS_ON_HOLD_AGENT_DISCONNECT"},
			{"Name":"CONTACTS_ON_HOLD_CUSTOMER_DISCONNECT"},
			{"Name":"CONTACTS_PUT_ON_HOLD"},
			{"Name":"CONTACTS_TRANSFERRED_OUT_EXTERNAL"},
			{"Name":"CONTACTS_TRANSFERRED_OUT_INTERNAL"},
			{"Name":"CONTACTS_QUEUED"},
			{"Name":"CONTACTS_QUEUED_BY_ENQUEUE"},
			{"Name":"CONTACTS_TRANSFERRED_OUT"},
			{"Name":"CONTACTS_TRANSFERRED_OUT_BY_AGENT"},
			{"Name":"CONTACTS_TRANSFERRED_OUT_FROM_QUEUE"},
			{"Name":"DELIVERY_ATTEMPTS"},
			{"Name":"DELIVERY_ATTEMPT_DISPOSITION_RATE"},
			{"Name":"EVALUATIONS_PERFORMED"},
			{"Name":"MAX_QUEUED_TIME"},
			{"Name":"PERCENT_AUTOMATIC_FAILS"},
			{"Name":"PERCENT_NON_TALK_TIME"},
			{"Name":"PERCENT_TALK_TIME"},
			{"Name":"PERCENT_TALK_TIME_AGENT"},
			{"Name":"PERCENT_TALK_TIME_CUSTOMER"},
			{"Name":"SUM_AFTER_CONTACT_WORK_TIME"},
			{"Name":"SUM_CONNECTING_TIME_AGENT"},
			{"Name":"CONTACTS_ABANDONED"},
			{"Name":"SUM_CONTACT_FLOW_TIME"},
			{"Name":"SUM_CONTACTS_DISCONNECTED"},
			{"Name":"SUM_HANDLE_TIME"},
			{"Name":"SUM_HOLD_TIME"},
			{"Name":"SUM_INTERACTION_AND_HOLD_TIME"},
			{"Name":"SUM_INTERACTION_TIME"},
			{"Name":"SUM_RETRY_CALLBACK_ATTEMPTS"}
		],
		"QUEUE": [
			{"Name":"ABANDONMENT_RATE"},
			{"Name":"AGENT_ADHERENT_TIME"},
			{"Name":"AGENT_ANSWER_RATE"},
			{"Name":"AGENT_NON_ADHERENT_TIME"},
			{"Name":"AGENT_NON_RESPONSE"},
			{"Name":"AGENT_NON_RESPONSE_WITHOUT_CUSTOMER_ABANDONS"},
			{"Name":"AGENT_SCHEDULE_ADHERENCE"},
			{"Name":"AGENT_SCHEDULED_TIME"},
			{"Name":"AVG_ABANDON_TIME"},
			{"Name":"AVG_ACTIVE_TIME"},
			{"Name":"AVG_AFTER_CONTACT_WORK_TIME"},
			{"Name":"AVG_AGENT_PAUSE_TIME"},
			{"Name":"AVG_CONTACT_DURATION"},
			{"Name":"AVG_CONVERSATION_DURATION"},
			{"Name":"AVG_DIALS_PER_MINUTE"},
			{"Name":"AVG_EVALUATION_SCORE"},
			{"Name":"AVG_GREETING_TIME_AGENT"},
			{"Name":"AVG_HANDLE_TIME"},
			{"Name":"AVG_HOLD_TIME"},
			{"Name":"AVG_HOLD_TIME_ALL_CONTACTS"},
			{"Name":"AVG_HOLDS"},
			{"Name":"AVG_INTERACTION_AND_HOLD_TIME"},
			{"Name":"AVG_INTERACTION_TIME"},
			{"Name":"AVG_INTERRUPTIONS_AGENT"},
			{"Name":"AVG_INTERRUPTION_TIME_AGENT"},
			{"Name":"AVG_NON_TALK_TIME"},
			{"Name":"AVG_QUEUE_ANSWER_TIME"},
			{"Name":"AVG_RESOLUTION_TIME"},
			{"Name":"AVG_TALK_TIME"},
			{"Name":"AVG_TALK_TIME_AGENT"},
			{"Name":"AVG_TALK_TIME_CUSTOMER"},
			{"Name":"AVG_WEIGHTED_EVALUATION_SCORE"},
			{"Name":"CONTACTS_CREATED"},
			{"Name":"CONTACTS_HANDLED"},
			{"Name":"CONTACTS_HANDLED_BY_CONNECTED_TO_AGENT"},
			{"Name":"CONTACTS_HOLD_ABANDONS"},
			{"Name":"CONTACTS_ON_HOLD_AGENT_DISCONNECT"},
			{"Name":"CONTACTS_ON_HOLD_CUSTOMER_DISCONNECT"},
			{"Name":"CONTACTS_PUT_ON_HOLD"},
			{"Name":"CONTACTS_TRANSFERRED_OUT_EXTERNAL"},
			{"Name":"CONTACTS_TRANSFERRED_OUT_INTERNAL"},
			{"Name":"CONTACTS_QUEUED"},
			{"Name":"CONTACTS_QUEUED_BY_ENQUEUE"},
			{"Name":"CONTACTS_TRANSFERRED_OUT"},
			{"Name":"CONTACTS_TRANSFERRED_OUT_BY_AGENT"},
			{"Name":"CONTACTS_TRANSFERRED_OUT_FROM_QUEUE"},
			{"Name":"DELIVERY_ATTEMPTS"},
			{"Name":"DELIVERY_ATTEMPT_DISPOSITION_RATE"},
			{"Name":"EVALUATIONS_PERFORMED"},
			{"Name":"MAX_QUEUED_TIME"},
			{"Name":"PERCENT_AUTOMATIC_FAILS"},
			{"Name":"PERCENT_CONTACTS_STEP_EXPIRED"},
			{"Name":"PERCENT_CONTACTS_STEP_JOINED"},
			{"Name":"PERCENT_NON_TALK_TIME"},
			{"Name":"PERCENT_TALK_TIME"},
			{"Name":"PERCENT_TALK_TIME_AGENT"},
			{"Name":"PERCENT_TALK_TIME_CUSTOMER"},
			{"Name":"STEP_CONTACTS_QUEUED"},
			{"Name":"SUM_AFTER_CONTACT_WORK_TIME"},
			{"Name":"SUM_CONNECTING_TIME_AGENT"},
			{"Name":"CONTACTS_ABANDONED"},
			{"Name":"SUM_CONTACT_FLOW_TIME"},
			{"Name":"SUM_CONTACTS_DISCONNECTED"},
			{"Name":"SUM_HANDLE_TIME"},
			{"Name":"SUM_HOLD_TIME"},
			{"Name":"SUM_INTERACTION_AND_HOLD_TIME"},
			{"Name":"SUM_INTERACTION_TIME"},
			{"Name":"SUM_RETRY_CALLBACK_ATTEMPTS"}
		],
		"GENERAL": [
			{"Name":"ABANDONMENT_RATE"},
			{"Name":"AGENT_ADHERENT_TIME"},
			{"Name":"AGENT_ANSWER_RATE"},
			{"Name":"AGENT_NON_ADHERENT_TIME"},
			{"Name":"AGENT_NON_RESPONSE"},
			{"Name":"AGENT_NON_RESPONSE_WITHOUT_CUSTOMER_ABANDONS"},
			{"Name":"AGENT_SCHEDULE_ADHERENCE"},
			{"Name":"AGENT_SCHEDULED_TIME"},
			{"Name":"AVG_ABANDON_TIME"},
			{"Name":"AVG_ACTIVE_TIME"},
			{"Name":"AVG_AFTER_CONTACT_WORK_TIME"},
			{"Name":"AVG_AGENT_PAUSE_TIME"},
			{"Name":"AVG_CONTACT_DURATION"},
			{"Name":"AVG_CONVERSATION_DURATION"},
			{"Name":"AVG_DIALS_PER_MINUTE"},
			{"Name":"AVG_EVALUATION_SCORE"},
			{"Name":"AVG_GREETING_TIME_AGENT"},
			{"Name":"AVG_HANDLE_TIME"},
			{"Name":"AVG_HOLD_TIME"},
			{"Name":"AVG_HOLD_TIME_ALL_CONTACTS"},
			{"Name":"AVG_HOLDS"},
			{"Name":"AVG_INTERACTION_AND_HOLD_TIME"},
			{"Name":"AVG_INTERACTION_TIME"},
			{"Name":"AVG_INTERRUPTIONS_AGENT"},
			{"Name":"AVG_INTERRUPTION_TIME_AGENT"},
			{"Name":"AVG_NON_TALK_TIME"},
			{"Name":"AVG_QUEUE_ANSWER_TIME"},
			{"Name":"AVG_RESOLUTION_TIME"},
			{"Name":"AVG_TALK_TIME"},
			{"Name":"AVG_TALK_TIME_AGENT"},
			{"Name":"AVG_TALK_TIME_CUSTOMER"},
			{"Name":"AVG_WEIGHTED_EVALUATION_SCORE"},
			{"Name":"CONTACTS_CREATED"},
			{"Name":"CONTACTS_HANDLED"},
			{"Name":"CONTACTS_HANDLED_BY_CONNECTED_TO_AGENT"},
			{"Name":"CONTACTS_HOLD_ABANDONS"},
			{"Name":"CONTACTS_ON_HOLD_AGENT_DISCONNECT"},
			{"Name":"CONTACTS_ON_HOLD_CUSTOMER_DISCONNECT"},
			{"Name":"CONTACTS_PUT_ON_HOLD"},
			{"Name":"CONTACTS_TRANSFERRED_OUT_EXTERNAL"},
			{"Name":"CONTACTS_TRANSFERRED_OUT_INTERNAL"},
			{"Name":"CONTACTS_QUEUED"},
			{"Name":"CONTACTS_QUEUED_BY_ENQUEUE"},
			{"Name":"CONTACTS_TRANSFERRED_OUT"},
			{"Name":"CONTACTS_TRANSFERRED_OUT_BY_AGENT"},
			{"Name":"CONTACTS_TRANSFERRED_OUT_FROM_QUEUE"},
			{"Name":"DELIVERY_ATTEMPTS"},
			{"Name":"DELIVERY_ATTEMPT_DISPOSITION_RATE"},
			{"Name":"EVALUATIONS_PERFORMED"},
			{"Name":"MAX_QUEUED_TIME"},
			{"Name":"PERCENT_AUTOMATIC_FAILS"},
			{"Name":"PERCENT_CONTACTS_STEP_EXPIRED"},
			{"Name":"PERCENT_CONTACTS_STEP_JOINED"},
			{"Name":"PERCENT_NON_TALK_TIME"},
			{"Name":"PERCENT_TALK_TIME"},
			{"Name":"PERCENT_TALK_TIME_AGENT"},
			{"Name":"PERCENT_TALK_TIME_CUSTOMER"},
			{"Name":"STEP_CONTACTS_QUEUED"},
			{"Name":"SUM_AFTER_CONTACT_WORK_TIME"},
			{"Name":"SUM_CONNECTING_TIME_AGENT"},
			{"Name":"CONTACTS_ABANDONED"},
			{"Name":"SUM_CONTACT_FLOW_TIME"},
			{"Name":"SUM_CONTACTS_DISCONNECTED"},
			{"Name":"SUM_HANDLE_TIME"},
			{"Name":"SUM_HOLD_TIME"},
			{"Name":"SUM_INTERACTION_AND_HOLD_TIME"},
			{"Name":"SUM_INTERACTION_TIME"},
			{"Name":"SUM_RETRY_CALLBACK_ATTEMPTS"}
		]
	}


    if grouping_type not in metrics:
        raise ValueError(f"Invalid grouping_type: {grouping_type}")

    queue_ids = [q["Id"] for q in queues]

    payload = {
        "ResourceArn": instance_arn,
        "StartTime": start_time,
        "EndTime": end_time,
        "Filters": [
            {
                "FilterKey": "QUEUE",
                "FilterValues": queue_ids
            }
        ],
        "Metrics": metrics[grouping_type],
        "MaxResults": 100,
		"Interval": {
			"IntervalPeriod": "FIFTEEN_MIN",
        },
    }

    if grouping_type in ["AGENT", "QUEUE"]:
        payload["Groupings"] = [grouping_type]

    metric_results = []
    while True:
        response = client.get_metric_data_v2(**payload)
        metric_results.extend(response.get("MetricResults", []))

        next_token = response.get("NextToken")
        if not next_token:
            break

        payload["NextToken"] = next_token

    return metric_results



# https://docs.aws.amazon.com/connect/latest/APIReference/API_GetCurrentUserData.html
def get_current_user_data(connect_client, instance_id, queues):

    queue_ids = [queue['Id'] for queue in queues]

    all_user_data = []

    params = {
        'InstanceId': instance_id,
        'Filters': {'Queues': queue_ids}, 
        'MaxResults': 100 
    }

    response = connect_client.get_current_user_data(**params)
    all_user_data.extend(response.get('UserDataList', []))

    while 'NextToken' in response and response['NextToken']:
        params['NextToken'] = response['NextToken']
        response = connect_client.get_current_user_data(**params)
        all_user_data.extend(response.get('UserDataList', []))
    
    return all_user_data



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
	try:

		connect_client = boto3.client(service_name='connect')
		kinesis_client = boto3.client(service_name='kinesis')
		instance_id = os.environ['CONNECT_INSTANCE_ID']
		instance_arn = connect_client.describe_instance(InstanceId=instance_id)["Instance"]["Arn"]
		queues = get_queues(connect_client, instance_id)
		
		#implement a call to the users to get their username/ info and use it on the indexation of the get_current_user_data 

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

		# Get get_metric_data_v2 records by queue
		metric_v2_data_by_queue = get_metric_data_v2(connect_client, instance_arn, queues, start_time, end_time_rounded, grouping_type="QUEUE")

		for r in metric_v2_data_by_queue:
			queue_id = r["Dimensions"].get("QUEUE")
			if queue_id:
				for queue in queues:
					if queue_id == queue["Id"]:
						r["Dimensions"]["Queue"] = {
							"Id": queue["Id"],
							"Name": queue["Name"],
						}
						break
				# Si el nombre fue agregado correctamente
				if "Queue" in r["Dimensions"]:
					record = {
						'Data': json.dumps(r, default=str).encode(),
						'PartitionKey': r["Dimensions"]["Queue"]["Name"]
					}
					all_metric_records_for_all_queues.append(record)

		# Get get_metric_data_v2 records by agent
		metric_data_by_agent = get_metric_data_v2(connect_client, instance_arn, queues, start_time, end_time_rounded, grouping_type="AGENT")

		for r in metric_data_by_agent:
			agent_id = r["Dimensions"].get("AGENT")
			if agent_id:
				r["Dimensions"]["Agent"] = {
					"Id": agent_id,
					"Name": agent_id,
				}

				record = {
					'Data': json.dumps(r, default=str).encode(),
					'PartitionKey': agent_id
				}
				all_metric_records_for_all_queues.append(record)
		

		#Get user real time data 
		user_data_list = get_current_user_data(connect_client, instance_id, queues)
		for user_data in user_data_list:
			user_record = {
				'Data': json.dumps(user_data, default=str).encode(),
				'PartitionKey': user_data['User']['Id'] #it does it with the user id but can be done with the queue_id if necesary 
			}
			all_metric_records_for_all_queues.append(user_record)
		
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

	except Exception as e:
		logger.error(f"Lambda execution failed {e}", exc_info=True)
		raise