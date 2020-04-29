import json
import slack
import boto3
import jmespath

STANDARD_CHANNEL = "#nuuday_ai_instances"

def send_slack_notice(event, context):
    print(f"event is: {json.dumps(event)}")
    state = event['detail']['state']
    instance_id = event['detail']['instance-id']
    
    client_session = boto3.session.Session()
    slack_token = get_secret(client_session)
    slack_client = slack.WebClient(token=slack_token)

    instance_name, slack_user = get_instance_info(client_session, instance_id)
    if slack_user:
      channel = slack_user
    else:
      channel = STANDARD_CHANNEL
    
    message = f"The ec2 with instance name {instance_name} is now {state}"
    send_slack_message(slack_client, channel, message)
    return {'status': 'SUCCESS'}

def get_secret(client_session):
    secret_name = "slack_api_token"
    region_name = "eu-central-1"

    # Create a Secrets Manager client
    secrets_client = client_session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    resp = secrets_client.get_secret_value(SecretId=secret_name)
    secret = resp['SecretString']
    secret = json.loads(secret)
    return secret['SLACK_API_TOKEN']


def get_instance_info(client_session, instance_id):
    ec2_client = client_session.client('ec2')
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    inst_dict = jmespath.search(
      "Reservations[].Instances[].{name: Tags[?Key=='Name'].Value | [0], slack_user: Tags[?Key=='SlackUser'].Value | [0]}[0]",
      response,
    )
    name = inst_dict['name']
    slack_user = inst_dict['slack_user']
    return name, slack_user


def send_slack_message(slack_client, channel, message):
  return slack_client.chat_postMessage(
    channel=channel,
    text=message
  )