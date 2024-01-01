#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# Created by Tibor Völcker (tiborvoelcker@hotmail.de) on 31.12.23
# Last modified by Tibor Völcker on 01.01.24
# Copyright (c) 2023 Tibor Völcker (tiborvoelcker@hotmail.de)

from datetime import date, datetime, timedelta

import googleapiclient.discovery
import pandas as pd
from auth import auth
from googleapiclient.discovery import Resource
from tqdm import tqdm
from wrapper import BAR_FORMAT, Wrapper


def get_subscriptions(client: Resource) -> pd.DataFrame:
    """Retrieve all subscriptions to logged in account.

    Args:
        client (Resource): The YouTube API Resource.

    Returns:
        pd.DataFrame: A Dataframe containing each channel title, ID and its upload playlist ID.
    """
    # Retrieve the list of subscriptions
    resource = Wrapper(client.subscriptions())  # type: ignore
    items = resource.list_all(part="snippet", mine=True)

    # This flattens the entire dictionary
    df = pd.json_normalize(items)
    subs = pd.DataFrame()
    subs[["channelId", "title"]] = df[["snippet.resourceId.channelId", "snippet.title"]]

    # Get upload playlists
    subs["uploadPlaylistId"] = get_upload_playlists(client, list(subs["channelId"]))

    return subs


def get_upload_playlists(client: Resource, channeld_ids: list[str]) -> pd.Series:
    """Get the upload playlist IDs for a list of channel IDs.

    Args:
        client (Resource): The YouTube API Resource.
        channeld_ids (list[str]): A list of all channel IDs to get the upload playlists for.

    Returns:
        pd.Series: The upload playlist IDs.
    """
    # Retrieve the list of channels
    resource = Wrapper(client.channels())  # type: ignore
    items = resource.list_all(part="contentDetails", id=channeld_ids)

    # This flattens the entire dictionary
    df = pd.json_normalize(items)
    return df["contentDetails.relatedPlaylists.uploads"]


def get_videos(client: Resource, playlist_id: str) -> pd.DataFrame:
    """Get all videos of a playlist published in the last year.

    The year is calculated as 365 days before today.

    Args:
        client (Resource): The YouTube API Resource.
        playlist_id (str): The playlist ID.

    Returns:
        pd.DataFrame: A DataFrame containing the video IDs publish datetime and playlist ID.
    """
    last_year = date.today() - timedelta(365)

    resource = Wrapper(client.playlistItems())  # type: ignore
    items = []
    # Iterate over each item to break early (better performance)
    for item in resource.yield_all(part="snippet,contentDetails", playlistId=playlist_id):
        if datetime.fromisoformat(item["snippet"]["publishedAt"]).date() < last_year:
            # Assume videos are sorted newest to oldest (validated by simple test)
            break
        items.append(item)

    # This flattens the entire dictionary
    df = pd.json_normalize(items)
    if df.empty:
        # Some playlists are empty
        return df

    videos = pd.DataFrame()
    videos["videoId"] = df["contentDetails.videoId"]
    videos["publishedAt"] = pd.to_datetime(df["snippet.publishedAt"])
    videos["playlistId"] = playlist_id

    return videos


def get_video_durations(client: Resource, video_ids: list[str]) -> pd.Series:
    """Get the video durations given a list of video IDs.

    Args:
        client (Resource): The YouTube API Resource.
        video_ids (list[str]): The list of video IDs.

    Returns:
        pd.Series: The video durations.
    """
    resource = Wrapper(client.videos())  # type: ignore
    items = resource.list_all(
        part="contentDetails",
        id=video_ids,
        progress_bar=True,
        desc="Get video durations",
    )

    # This flattens the entire dictionary
    df = pd.json_normalize(items)
    return pd.to_timedelta(df["contentDetails.duration"])


def aggregate_uploads(videos: pd.DataFrame) -> pd.DataFrame:
    """Aggregate data for playlists.

    Aggregates the count and complete duration of a playlist, as well as publishing date of the
    first and last video.

    Args:
        videos (pd.DataFrame): The videos. Need to have a 'playlistId', 'duration' and 'publishedAt'
            column.

    Returns:
        pd.DataFrame: The aggregated data.
    """
    agg = pd.DataFrame()
    agg[["videoCount", "contentLength"]] = videos.groupby("playlistId")["duration"].agg(
        ["count", "sum"]
    )
    agg[["firstPublished", "lastPublished"]] = videos.groupby("playlistId")["publishedAt"].agg(
        ["min", "max"]
    )

    return agg


if __name__ == "__main__":
    # Get credentials
    creds = auth()

    # Create a YouTube API client
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)

    # Get all subscribed channels
    subs = get_subscriptions(youtube)

    # Get all videos
    videos = pd.DataFrame()
    for playlist_id in tqdm(
        subs["uploadPlaylistId"], desc="Get upload playlists", bar_format=BAR_FORMAT
    ):
        videos = pd.concat([videos, get_videos(youtube, playlist_id)], ignore_index=True)

    # Get video durations
    videos["duration"] = get_video_durations(youtube, list(videos["videoId"]))

    # Aggregate data for playlists
    subs = subs.join(aggregate_uploads(videos), on="uploadPlaylistId")

    # Calculate average content length
    avg_content = (subs["contentLength"].sum() / 365).total_seconds()
    print(
        "Avg. content length per day: "
        f"{avg_content // 3600:.0f} hours {round(avg_content % 3600 / 60)} minutes"
    )
