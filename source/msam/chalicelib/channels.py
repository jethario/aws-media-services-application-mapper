# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This file contains helper functions related to channels.
"""

import os
from urllib.parse import unquote

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from botocore.config import Config

import chalicelib.settings as msam_settings

# table names generated by CloudFormation
CHANNELS_TABLE_NAME = os.environ["CHANNELS_TABLE_NAME"]

# user-agent config
STAMP = os.environ["BUILD_STAMP"]
MSAM_BOTO3_CONFIG = Config(
    user_agent="aws-media-services-applications-mapper/{stamp}/channels.py".
    format(stamp=STAMP))

# DynamoDB
DYNAMO_RESOURCE = boto3.resource("dynamodb", config=MSAM_BOTO3_CONFIG)


def delete_channel_nodes(name):
    """
    API entry point to delete a channel.
    """
    try:
        name = unquote(name)
        table_name = CHANNELS_TABLE_NAME
        table = DYNAMO_RESOURCE.Table(table_name)
        # update the settings object with the name
        name_list = msam_settings.get_setting("channels")
        if not name_list:
            name_list = []
        if name in name_list:
            name_list.remove(name)
            msam_settings.put_setting("channels", name_list)
        # remove the members
        try:
            response = table.query(
                ProjectionExpression="channel,id",
                KeyConditionExpression=Key('channel').eq(name))
            items = response.get("Items", [])
            while "LastEvaluatedKey" in response:
                response = table.query(
                    ProjectionExpression="channel,id",
                    KeyConditionExpression=Key('channel').eq(name),
                    ExclusiveStartKey=response["LastEvaluatedKey"])
                items = items + response.get("Items", [])
            # return the response or an empty object
            for item in items:
                table.delete_item(Key={
                    "channel": item["channel"],
                    "id": item["id"]
                })
            print("channel items deleted, channel list updated")
        except ClientError:
            print("not found")
        response = {"message": "done"}
    except ClientError as outer_error:
        # send the exception back in the object
        print(outer_error)
        response = {"exception": str(outer_error)}
    return response


def get_channel_list():
    """
    Return all the current channel names.
    """
    channels = msam_settings.get_setting("channels")
    if not channels:
        channels = []
    return channels


def set_channel_nodes(name, node_ids):
    """
     API entry point to set the nodes for a given channel name.
    """
    try:
        name = unquote(name)
        table = DYNAMO_RESOURCE.Table(CHANNELS_TABLE_NAME)
        # print(request.json_body)
        # node_ids = request.json_body
        # write the channel nodes to the database
        for node_id in node_ids:
            item = {"channel": name, "id": node_id}
            table.put_item(Item=item)
        # update the list of channels in settings
        name_list = msam_settings.get_setting("channels")
        if not name_list:
            name_list = []
        if name not in name_list:
            name_list.append(name)
            msam_settings.put_setting("channels", name_list)
        result = {"message": "saved"}
        print(result)
    except ClientError as error:
        # send the exception back in the object
        print(error)
        result = {"exception": str(error)}
    return result


def get_channel_nodes(name):
    """
    API entry point to get the nodes for a given channel name.
    """
    try:
        name = unquote(name)
        table_name = CHANNELS_TABLE_NAME
        table = DYNAMO_RESOURCE.Table(table_name)
        try:
            # get the settings object
            response = table.query(
                KeyConditionExpression=Key('channel').eq(name))
            print(response)
            # return the response or an empty object
            if "Items" in response:
                settings = response["Items"]
            else:
                settings = []
            print("retrieved")
        except ClientError:
            print("not found")
            settings = []
    except ClientError as outer_error:
        # send the exception back in the object
        print(outer_error)
        settings = {"exception": str(outer_error)}
    return settings


def delete_all_channels():
    """
    Delete all tiles (channels) from the database
    """
    try:
        table = DYNAMO_RESOURCE.Table(CHANNELS_TABLE_NAME)
        # empty the value in settings
        msam_settings.put_setting("channels", [])
        # empty the channels table
        response = table.scan(ProjectionExpression="channel,id")
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = table.scan(
                ProjectionExpression="channel,id",
                ExclusiveStartKey=response["LastEvaluatedKey"])
            items = items + response.get("Items", [])
        for item in items:
            table.delete_item(Key={
                "channel": item["channel"],
                "id": item["id"]
            })
        response = {"message": "done"}
    except ClientError as client_error:
        print(client_error)
        response = {"message": str(client_error)}
    return response