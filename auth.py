#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# Taken from https://developers.google.com/people/quickstart/python
# Modified by Tibor Völcker (tiborvoelcker@hotmail.de)

from pathlib import Path

from google.auth.external_account_authorized_user import Credentials as ExtCredentials
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]


def auth() -> Credentials | ExtCredentials:
    """Get the users credentials."""
    auth_dir = (Path(__file__).parent / "auth").resolve()

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if (auth_dir / "token.json").exists():
        creds = Credentials.from_authorized_user_file(auth_dir / "token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(auth_dir / "credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(auth_dir / "token.json", "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return creds
