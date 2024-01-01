#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# Created by Tibor Völcker (tiborvoelcker@hotmail.de) on 01.01.24
# Last modified by Tibor Völcker on 01.01.24
# Copyright (c) 2024 Tibor Völcker (tiborvoelcker@hotmail.de)

import logging
import math
from typing import Generator

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError
from tqdm import tqdm, trange

BAR_FORMAT = "{l_bar}{bar}| [{remaining}]"


class Wrapper:
    """Wrapper for `googleapiclient.discovery.Resource`.

    Adds docstrings and annotations and the `yield_all` and `list_all` methods.
    """

    def __init__(self, resource: Resource):
        """Initializes the class.

        Args:
            resource (Resource): The original Resource.
                Must implement the `list` and `list_next` methods.

        Raises:
            ValueError: If the Resource does not implement the `list` and
                `list_next` methods.
        """
        if not (
            hasattr(resource, "list")
            and callable(getattr(resource, "list"))
            and hasattr(resource, "list_next")
            and callable(getattr(resource, "list_next"))
        ):
            raise ValueError("Resource must implement the `list` and`list_next` methods")

        self._resource = resource

    def _yield_all(self, progress_bar=False, desc="", **kwargs) -> Generator[dict, None, None]:
        """Generator which yields the items from all pages.

        This function will request each page from the API and yield each
        item after another.

        Yields:
            Generator[dict, None, None]: The items.
        """
        kwargs.update(maxResults=50)
        req = self._resource.list(**kwargs)  # type: ignore
        try:
            with tqdm(disable=not progress_bar, bar_format=BAR_FORMAT, desc=desc) as pbar:
                while req is not None:
                    res = req.execute()

                    pbar.total = math.ceil(res["pageInfo"]["totalResults"] / 50)
                    pbar.update()

                    for item in res["items"]:
                        yield item

                    req = self._resource.list_next(req, res)  # type: ignore

        except HttpError as e:
            if e.status_code == 404:
                return
            logging.error(e)
            raise

    def yield_all(self, progress_bar=False, desc="", **kwargs) -> Generator[dict, None, None]:
        """Generator which yields the items from all pages.

        This function will request each page from the API and yield each
        item after another.

        Args:
            progress_bar (bool, optional): If a progress bar should be shown.
                Defaults to False.
            desc (str, optional): The description to the progess bar.
                Defaults to "".
            kwargs (dict[str, Unknown]): Arguments for the request.
                See the resource's `list` method.

        Yields:
            Generator[dict, None, None]: The items.
        """
        if "id" in kwargs and len(kwargs["id"]) > 50:
            # If more than 50 ID's are requested, they need to be split into
            # multiple calls of 50 ID's
            ids = kwargs.pop("id")
            for i in trange(
                0,
                len(ids),
                50,
                unit_scale=50,
                disable=not progress_bar,
                desc=desc,
                bar_format=BAR_FORMAT,
            ):
                # This should most likely be only one page
                yield from self._yield_all(**kwargs, id=ids[i : i + 50])
        else:
            yield from self._yield_all(**kwargs, progress_bar=progress_bar, desc=desc)

    def list_all(self, **kwargs) -> list[dict]:
        """List with the items from all pages.

        This function will request each page from the API and return each
        item in a list.

        Args:
            progress_bar (bool, optional): If a progress bar should be shown.
                Defaults to False.
            desc (str, optional): The description to the progess bar.
                Defaults to "".
            kwargs (dict[str, Unknown]): Arguments for the request.
                See the resource's `list` method.

        Returns:
            list[dict]: The items.
        """
        return list(self.yield_all(**kwargs))
