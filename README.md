# YouTube-Content-Length
A small Python script that calculates the average length of daily content from subscriptions.

The average could be calculated in many ways. This script is using the sum of the video durations published by subscribed channels in the last 365 days, and then dividing by 365 days.

> One could also use the average of the last month or average between the first and last video published by each channel.

## Setup Google Cloud
The script used the YouTube API. To set it up, follow these steps:
* Create an account at [Google Cloud](https://console.cloud.google.com/), and create a project.
* Search for the [YouTube Data API v3](https://console.cloud.google.com/apis/library/youtube.googleapis.com) and activate it.
* Create an [OAuth-Client-ID](https://console.cloud.google.com/apis/credentials/oauthclient). You may restrict it to only use the YouTube Data API v3. Save the JSON file in the `auth` directory next to the `example_token.json` as `token.json`.
* Lastly, if the app is in `Testing` mode, you need to add your account as a test user. Go to the [OAuth consent screen setting](https://console.cloud.google.com/apis/credentials/consent) and add your e-mail as a test user.
