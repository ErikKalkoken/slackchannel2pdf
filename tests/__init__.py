import inspect
import json
import os

_currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


def slack_response(data, ok=True, error=None) -> str:
    if not ok:
        return {"ok": False, **{"error": error}}
    else:
        return {"ok": True, **data}


class SlackResponseStub:
    def __init__(self, data, ok=True) -> None:
        self.data = slack_response(data, ok)


class SlackClientStub:
    def __init__(self, team: str) -> None:
        self._team = str(team)
        with open(f"{_currentdir}/slack_data.json", "r", encoding="utf-8") as f:
            self._slack_data = json.load(f)

    def auth_test(self) -> str:
        return SlackResponseStub(self._slack_data[self._team]["auth_test"])

    def bots_info(self, bot) -> str:
        return slack_response({}, ok=False)

    def conversations_replies(
        self, channel, ts, limit, oldest, latest, cursor=None
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

    def conversations_history(self, channel, limit, oldest, latest, cursor=None) -> str:
        if channel in self._slack_data[self._team]["conversations_history"]:
            messages = self._slack_data[self._team]["conversations_history"][channel]
            return slack_response(self._messages_to_response(messages))
        else:
            return slack_response(None, ok=False, error="Channel not found")

    @staticmethod
    def _messages_to_response(messages: list) -> dict:
        return {"messages": messages, "has_more": False}

    def conversations_list(self, types) -> str:
        return slack_response(self._slack_data[self._team]["conversations_list"])

    def users_info(self, user, include_locale=None) -> str:
        users = {
            obj["id"]: obj
            for obj in self._slack_data[self._team]["users_list"]["members"]
        }
        if user in users:
            return slack_response({"user": users[user]})
        else:
            return slack_response(None, ok=False, error="User not found")

    def users_list(self) -> str:
        return slack_response(self._slack_data[self._team]["users_list"])

    def usergroups_list(self) -> str:
        return slack_response(self._slack_data[self._team]["usergroups_list"])
