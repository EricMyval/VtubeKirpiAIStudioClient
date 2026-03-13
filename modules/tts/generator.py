import threading
from modules.runtime.incoming_event_queue import incomingEventQueue
from modules.runtime.prepared_event_queue import preparedEventQueue
from modules.runtime.prepared_event import PreparedEvent
from modules.tts.runtime import tts_runtime
from modules.utils.constant import PLATFORM_TYPE_TWITCH_POINTS

class TTSGenerator:
    def __init__(self):
        threading.Thread(
            target=self._loop,
            daemon=True
        ).start()

    def _loop(self):
        while True:
            event = incomingEventQueue.get_event()
            try:
                segment_queue = None
                if event.get("platform") != PLATFORM_TYPE_TWITCH_POINTS:
                    text = event.get("formatted_text")
                    voice_file = event.get("voice_file_path")
                    voice_text = event.get("voice_reference_text")
                    if text and voice_file and voice_text:
                        segment_queue = tts_runtime.generate(
                            text,
                            voice_file,
                            voice_text
                        )
                preparedEventQueue.add(
                    PreparedEvent(event, segment_queue)
                )
            except Exception as e:
                print("[TTSGenerator]", e)
            finally:
                incomingEventQueue.task_done()

ttsGenerator = TTSGenerator()