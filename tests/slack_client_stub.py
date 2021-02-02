import inspect
import json
import os

_currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


def chunks(lst, size):
    """Yield successive sized chunks from lst."""
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def slack_response(data: dict, ok: bool = True, error: str = None) -> str:
    if not ok:
        return {"ok": False, **{"error": error}}
    else:
        return {"ok": True, **data}


class SlackResponseStub:
    def __init__(self, data, ok=True) -> None:
        self.data = slack_response(data, ok)


class SlackClientStub:
    def __init__(self, team: str, page_size: int = None) -> None:
        self._team = str(team)
        self._page_size = int(page_size) if page_size else None
        self._page_counts = {"conversations_list": 0}
        with open(f"{_currentdir}/slack_data.json", "r", encoding="utf-8") as f:
            self._slack_data = json.load(f)

    def _paging(self, data, key, cursor=None) -> str:
        if not self._page_size:
            return slack_response({key: data})
        else:
            data_chunks = list(chunks(data, self._page_size))
            if cursor is None:
                cursor = 0

            response = {key: data_chunks[cursor]}
            if len(data_chunks) > cursor + 1:
                response["response_metadata"] = {"next_cursor": cursor + 1}

            return slack_response(response)

    def auth_test(self) -> str:
        return SlackResponseStub(self._slack_data[self._team]["auth_test"])

    def bots_info(self, bot) -> str:
        return slack_response({}, ok=False)

    def conversations_replies(
        self, channel, ts, limit=None, oldest=None, latest=None, cursor=None
    ) -> str:
        if (
            channel in self._slack_data[self._team]["conversations_replies"]
            and ts in self._slack_data[self._team]["conversations_replies"][channel]
        ):
            messages = self._slack_data[self._team]["conversations_replies"][channel][
                ts
            ]
            return slack_response(self._messages_to_response(messages))
        else:
            return slack_response(None, ok=False, error="Thread not found")

    def conversations_history(
        self, channel, limit=None, oldest=None, latest=None, cursor=None
    ) -> str:
        if channel in self._slack_data[self._team]["conversations_history"]:
            messages = self._slack_data[self._team]["conversations_history"][channel]
            return self._paging(messages, "messages", cursor)
        else:
            return slack_response(None, ok=False, error="Channel not found")

    @staticmethod
    def _messages_to_response(messages: list) -> dict:
        return {"messages": messages, "has_more": False}

    def conversations_list(self, types, limit=None, cursor=None) -> str:
        return self._paging(
            self._slack_data[self._team]["conversations_list"]["channels"],
            "channels",
            cursor,
        )

    def users_info(self, user, include_locale=None) -> str:
        users = {
            obj["id"]: obj
            for obj in self._slack_data[self._team]["users_list"]["members"]
        }
        if user in users:
            return slack_response({"user": users[user]})
        else:
            return slack_response(None, ok=False, error="User not found")

    def users_list(self, limit=None) -> str:
        return slack_response(self._slack_data[self._team]["users_list"])

    def usergroups_list(self) -> str:
        return slack_response(self._slack_data[self._team]["usergroups_list"])
