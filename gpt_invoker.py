import datetime
import hashlib
import json
import logging
import os
import re
import sqlite3
import threading
import traceback
from typing import Optional

import colorlog
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

GPT_INVOKER_VERSION = "0.1.2"

logger = logging.getLogger(__name__)


def _init_logger():
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter("%(log_color)s%(levelname)s: %(name)s %(message)s")
    )
    handler.setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)


_init_logger()


RESPONSE_CODE_PATTERN = re.compile("```(?:\\w+\\s+)?(.*?)```", re.DOTALL)
RESPONSE_INVARIANT_PATTERN = re.compile("<invariant>(.*?)</invariant>")
RESPONSE_FIELD_PATTERN = re.compile("<field>(.*?)</field>")
RESPONSE_JSON_PATTERN = re.compile("```json\n(.*?)```", re.DOTALL)
RESPONSE_JAVA_PATTERN = re.compile("```java\n(.*?)```", re.DOTALL)


GPT_PRICE_TABLE = {
    "default": (5, 20, 2.5),
    "gpt-4.1": (2, 8, 0.5),
    "gpt-4.1-mini": (0.4, 1.6, 0.1),
    "gpt-4.1-nano": (0.1, 0.4, 0.025),
    "gpt-4o": (2.5, 10, 1.25),
    "gpt-4o-mini": (0.15, 0.6, 0.075),
}


class Usage:
    def __init__(self, model_name: Optional[str] = None):
        self.clear()

        if model_name not in GPT_PRICE_TABLE:
            logger.warning(
                f"Model {model_name} not found in GPT price table, using GPT-4o prices for evaluation."
            )
            model_name = "default"
        self.model_name = model_name

        self.lock = threading.Lock()

    def clear(self):
        self.completion_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens_cached = 0
        self.prompt_tokens_cached = 0

    def update(self, result: ChatCompletion, is_cached: bool = False):
        usage = result.usage
        if usage is None:
            return

        with self.lock:
            if not is_cached:
                self.completion_tokens += usage.completion_tokens
                self.prompt_tokens += usage.prompt_tokens
            else:
                self.completion_tokens_cached += usage.completion_tokens
                self.prompt_tokens_cached += usage.prompt_tokens

    def __str__(self):
        model_str = ""
        if self.model_name == "default":
            model_str = "(Estimated by GPT-4o prices)"

        input_tokens = self.prompt_tokens
        output_tokens = self.completion_tokens
        input_tokens_cached = self.prompt_tokens_cached
        output_tokens_cached = self.completion_tokens_cached

        input_tokens_price = (
            input_tokens * GPT_PRICE_TABLE[self.model_name][0] / 1000000
        )
        output_tokens_price = (
            output_tokens * GPT_PRICE_TABLE[self.model_name][1] / 1000000
        )
        input_tokens_cached_price = (
            input_tokens_cached * GPT_PRICE_TABLE[self.model_name][0] / 1000000
        )
        output_tokens_cached_price = (
            output_tokens_cached * GPT_PRICE_TABLE[self.model_name][1] / 1000000
        )

        total_tokens = (
            input_tokens + output_tokens + input_tokens_cached + output_tokens_cached
        )
        total_price = (
            input_tokens_price
            + output_tokens_price
            + input_tokens_cached_price
            + output_tokens_cached_price
        )

        return (
            f"{model_str} Input: {input_tokens} tokens ({input_tokens_price:.4f} USD), "
            f"Output: {output_tokens} tokens ({output_tokens_price:.4f} USD), "
            f"Cached Input: {input_tokens_cached} tokens ({input_tokens_cached_price:.4f} USD), "
            f"Cached Output: {output_tokens_cached} tokens ({output_tokens_cached_price:.4f} USD), "
            f"Total: {total_tokens} tokens ({total_price:.4f} USD"
        )


class GPTInvoker:
    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gpt-4.1",
        top_p: float = 0.9,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        api_host: str = "https://api.openai.com",
        gpt_cache_path: Optional[str] = None,
        read_from_cache: bool = True,
        write_to_cache: bool = True,
        gpt_log_path: Optional[str] = None,
        write_gpt_log: bool = True,
        gpt_dump_folder: Optional[str] = None,
        dump_gpt_log: bool = True,
    ) -> None:
        cur_path = os.path.dirname(os.path.abspath(__file__))
        if gpt_cache_path is None:
            gpt_cache_path = os.path.join(cur_path, "gpt_cache.db")
        if gpt_log_path is None:
            gpt_log_path = os.path.join(cur_path, "gpt_log.txt")
        if gpt_dump_folder is None:
            gpt_dump_folder = os.path.join(cur_path, "gpt_dump")

        self.gpt_cache_path = gpt_cache_path
        self.gpt_log_path = gpt_log_path
        self.gpt_dump_folder = gpt_dump_folder
        self.read_from_cache = read_from_cache
        self.write_to_cache = write_to_cache
        self.enable_cache = read_from_cache or write_to_cache
        self.write_gpt_log = write_gpt_log
        self.dump_gpt_log = dump_gpt_log

        self.client = OpenAI(api_key=api_key, base_url=api_host)
        self.model = model
        self.model_args = {
            "top_p": top_p,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        self.gpt_cache = None
        self._init_gpt_cache()

        if self.gpt_log_path is None:
            self.gpt_log = None
        else:
            self.gpt_log = open(self.gpt_log_path, "ab", buffering=0)

        self.prompt_organize_input_system = None
        self.prompt_organize_input_user = None
        self.prompt_organize_input_error = None

        self.usage = Usage(self.model)

    def _init_gpt_cache(self):
        if not self.enable_cache:
            return

        check_thread = True
        if sqlite3.threadsafety == 3:
            check_thread = False
        else:
            logger.warning(
                "SQLite threadsafety is not 3, which may cause issues with concurrent access."
            )

        self.gpt_cache = sqlite3.connect(
            self.gpt_cache_path, check_same_thread=check_thread
        )

        cursor = self.gpt_cache.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS gpt_cache (cache_id PRIMARY KEY, cache_digest TEXT, cache_prompt TEXT, cache_response TEXT)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS cache_digest_index ON gpt_cache (cache_digest)"
        )
        try:
            self.gpt_cache.commit()
        except sqlite3.OperationalError:
            pass

        seperate_token = "|9ZPA|"
        model_args_sorted = sorted(self.model_args.items())
        msg_concat = []
        for key, value in model_args_sorted:
            msg_concat.append(seperate_token)
            msg_concat.append(key)
            msg_concat.append(seperate_token)
            msg_concat.append(repr(value))
        msg_concat.append(seperate_token)
        msg_concat.append(self.model)
        self.model_args_str = "".join(msg_concat)

    def _query_gpt_cache(
        self, msg_digest: str, msg_concat: str
    ) -> Optional[ChatCompletion]:
        if self.gpt_cache is None or not self.read_from_cache:
            return None

        cursor = self.gpt_cache.cursor()
        cursor.execute(
            "SELECT cache_prompt, cache_response FROM gpt_cache WHERE cache_digest = ? ",
            (msg_digest,),
        )
        response = cursor.fetchone()
        if response:
            cache_prompt_q, cache_response = response
            if cache_prompt_q == msg_concat:
                return ChatCompletion(**json.loads(cache_response))
        return None

    def _put_gpt_cache(
        self, msg_digest: str, msg_concat: str, msg_response: ChatCompletion
    ):
        if self.gpt_cache is None or not self.write_to_cache:
            return

        try:
            cursor = self.gpt_cache.cursor()
            cursor.execute(
                "SELECT cache_prompt FROM gpt_cache WHERE cache_digest = ? ",
                (msg_digest,),
            )
            response = cursor.fetchone()
            if response:
                cache_prompt_q = response[0]
                if cache_prompt_q == msg_concat:
                    cursor.execute(
                        "UPDATE gpt_cache SET cache_response = ? WHERE cache_digest = ?",
                        (msg_response.model_dump_json(), msg_digest),
                    )
                else:
                    return
            else:
                cursor.execute(
                    "INSERT INTO gpt_cache (cache_digest, cache_prompt, cache_response) VALUES (?, ?, ?)",
                    (msg_digest, msg_concat, msg_response.model_dump_json()),
                )
            try:
                self.gpt_cache.commit()
            except sqlite3.OperationalError:
                pass
        except Exception:
            logger.error("Error while writing to GPT cache", exc_info=True)

    def _msg_digest(self, message: list[ChatCompletionMessageParam]) -> tuple[str, str]:
        msg_concat = [self.model_args_str]
        msg_concat.append(json.dumps(message, ensure_ascii=False))
        msg_concat = "".join(msg_concat)
        msg_digest = hashlib.sha1(msg_concat.encode()).hexdigest()
        return msg_digest, msg_concat

    def generate_inner(
        self, messages: list[ChatCompletionMessageParam]
    ) -> ChatCompletion:
        response = self.client.chat.completions.create(
            model=self.model, messages=messages, **self.model_args
        )
        return response

    def generate_inner_stream(self, messages: list[ChatCompletionMessageParam]) -> str:
        response = self.client.chat.completions.create(
            model=self.model, messages=messages, stream=True, **self.model_args
        )
        all_text = []
        for sse_chunk in response:
            if len(sse_chunk.choices) > 0:
                content = sse_chunk.choices[0].delta.content
                if content is not None:
                    all_text.append(content)
        response = "".join(all_text)
        return response

    def generate_all_res(
        self, messages: list[ChatCompletionMessageParam], ignore_cache=False
    ) -> ChatCompletion:
        msg_digest, msg_concat = None, None
        if (self.read_from_cache and not ignore_cache) or self.write_to_cache:
            msg_digest, msg_concat = self._msg_digest(messages)
            if self.read_from_cache and not ignore_cache:
                gpt_cache = self._query_gpt_cache(msg_digest, msg_concat)
                if gpt_cache is not None:
                    self.dump_log(messages, gpt_cache, True)
                    self.usage.update(gpt_cache, is_cached=True)
                    return gpt_cache

        try:
            response = self.generate_inner(messages)
        except Exception:
            logger.error("Error while generating response", exc_info=True)
            err_msg = traceback.format_exc()
            self.dump_log(messages, None, False, True, err_msg)
            raise

        self.usage.update(response)

        if self.enable_cache and self.write_to_cache:
            assert msg_digest is not None and msg_concat is not None
            self._put_gpt_cache(msg_digest, msg_concat, response)

        self.dump_log(messages, response, False)

        return response

    def generate(self, messages: list[ChatCompletionMessageParam]) -> str:
        response = self.generate_all_res(messages)
        choices = response.choices
        if len(choices) == 0:
            raise ValueError("No choices in the response")
        if len(choices) > 1:
            raise ValueError("Multiple choices in the response")
        choice = choices[0]
        finish_reason = choice.finish_reason
        if finish_reason != "stop":
            raise ValueError(f"Finish reason is not 'stop': {finish_reason}")
        msg = choice.message
        if msg.refusal is not None:
            logger.warning(f"GPT refused to answer: {msg.refusal}.")
        if msg.content is None:
            if msg.refusal is not None:
                raise ValueError("Refused Message: " + msg.refusal)
            raise ValueError("No content in the response message")
        content = msg.content
        return content

    def extract_code(self, message: str) -> str:
        code_matches = RESPONSE_CODE_PATTERN.findall(message)
        if len(code_matches) == 0:
            raise ValueError("No code block found in the response")
        if len(code_matches) > 1:
            raise ValueError("Multiple code blocks found in the response")

        code = code_matches[0]

        return code

    def extract_invs(self, message: str) -> list[str]:
        invariant_matches = RESPONSE_INVARIANT_PATTERN.findall(message)
        return invariant_matches

    def extract_json(self, message: str):
        json_matches = RESPONSE_JSON_PATTERN.findall(message)
        if len(json_matches) == 0:
            raise ValueError("No json block found in the response")
        if len(json_matches) > 1:
            raise ValueError("Multiple json blocks found in the response")
        json_str = json_matches[0]
        json_obj = json.loads(json_str)
        return json_obj

    def extract_java(self, message: str):
        java_matches = RESPONSE_JAVA_PATTERN.findall(message)
        if len(java_matches) == 0:
            raise ValueError("No java block found in the response")
        if len(java_matches) > 1:
            raise ValueError("Multiple java blocks found in the response")
        java_str = java_matches[0]
        return java_str

    def dump_log(
        self,
        messages: list[ChatCompletionMessageParam],
        output: Optional[ChatCompletion],
        is_from_cache: bool,
        is_error: bool = False,
        err_msg: Optional[str] = None,
    ):
        # if self.gpt_dump_folder is None: return
        if self.gpt_dump_folder is not None:
            all_msgs = str(messages)
            md5 = hashlib.md5(all_msgs.encode()).hexdigest()

            now_time = datetime.datetime.now()
            now = now_time.strftime("%Y-%m-%d-%H-%M-%S-%f")
            idx = 0
            cache_str = "-C" if is_from_cache else "-N"
            if is_error:
                cache_str = "-E"
            while True:
                folder = now_time.strftime("%Y-%m-%d/%H" + cache_str)
                os.makedirs(os.path.join(self.gpt_dump_folder, folder), exist_ok=True)
                full_name = os.path.join(
                    self.gpt_dump_folder, folder, f"{now}-{md5}-{idx}.md"
                )
                if not os.path.exists(full_name):
                    break
                idx += 1

            with open(full_name, "w", encoding="utf-8") as f:
                if is_error:
                    f.write(f"ERROR Generation: \n{err_msg}\n")
                if output is not None:
                    f.write("------------ Response Meta Info ------------\n")
                    f.write(f"Created: {output.created}\n")
                    f.write(f"Model: {output.model}\n")
                    f.write(f"ServiceTier: {output.service_tier}\n")
                    f.write(f"SystemFingerprint: {output.system_fingerprint}\n")
                    f.write(f"Usage: {output.usage}\n")
                for msg in messages:
                    role = msg["role"]
                    f.write(f"\n\n------------ Input Message {role} ------------\n")
                    other_fields = {}
                    for k, v in msg.items():
                        if k == "role" or k == "content":
                            continue
                        other_fields[k] = v
                    if len(other_fields) > 0:
                        other_fields = json.dumps(
                            other_fields, ensure_ascii=False, indent=2
                        )
                        f.write(f"Fields: {other_fields}\n\n")
                    if "content" in msg:
                        f.write(msg["content"])  # type: ignore
                if output is not None:
                    f.write("\n\n------------ Response Message ------------\n")
                    choices = output.choices
                    if len(choices) == 0:
                        f.write("No choices in the response.\n")
                    for choice in choices:
                        finish_reason = choice.finish_reason
                        index = choice.index
                        log_probs = choice.logprobs
                        if log_probs is not None:
                            log_probs = log_probs.model_dump_json()
                        else:
                            log_probs = "None"
                        f.write(
                            f"\n\n------------ Choice {index} {finish_reason} Probs: {log_probs} ------------\n"
                        )
                        message = choice.message

                        content = message.content
                        refusal = message.refusal
                        annotations = message.annotations
                        audio = message.audio
                        function_call = message.function_call
                        tool_calls = message.tool_calls

                        if content is not None:
                            f.write(f"{content}\n")

                        if refusal is not None:
                            f.write(f"Refusal: {refusal}\n")

                        if annotations is not None and len(annotations) > 0:
                            f.write("Annotations:\n")
                            for annotation in annotations:
                                f.write(f"{annotation.model_dump_json()}\n")

                        if audio is not None:
                            f.write(f"Audio: {audio.model_dump_json()}\n")

                        if function_call is not None:
                            f.write(
                                f"Function Call: {function_call.model_dump_json()}\n"
                            )

                        if tool_calls is not None:
                            f.write("Tool Calls:\n")
                            for tool_call in tool_calls:
                                f.write(f"{tool_call.model_dump_json()}\n")

        if self.gpt_log is not None:
            pass
            messages_str = json.dumps(messages, ensure_ascii=False)
            if output is not None:
                output_str = output.model_dump_json()
            else:
                output_str = None
            if output is not None:
                output_str = output.model_dump_json()
            else:
                output_str = None
            log_content = {
                "timestamp": datetime.datetime.now().isoformat(),
                "messages": messages_str,
                "output": output_str,
                "is_from_cache": is_from_cache,
                "is_error": is_error,
                "error_message": err_msg,
            }
            log_content_str = json.dumps(log_content, ensure_ascii=False) + "\n"
            self.gpt_log.write(log_content_str.encode("utf-8"))


def main():
    invoker = GPTInvoker(
        model="gpt-4.1",
        api_key=os.getenv("LLM_API_KEY"),
        api_host="https://yunwu.ai/v1",
        max_tokens=1024,
        dump_gpt_log=True,
    )

    response = invoker.generate(
        [
            {"role": "user", "content": "Hello, how are you doing today?"},
        ]
    )
    print(response)

    print(invoker.usage)


if __name__ == "__main__":
    main()
