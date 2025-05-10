in ```async def a_call_llm(websocket, data)```, when we loop on LLM response chunk of texts in ```for chunk in llm_instance.llm._stream(prompt):``` we start capturing the text in ```            elif capturing_text:
                at_least_one_chunk_has_been_sent = True
                text += chunk_text``` in the variable 'text'.
Then when all the text (what the text to speech need to 'say'), we send the text to the tts_queue to be converted into speech in ```        # Instead of creating a new thread, queue the TTS work
        tts_queue.put((text, ''.join(filter(str.isdigit, speaker_id)), tts_callback))```.

What I would like to change is while capturing the text parsing chunk of texts, if a chunk has a '.' or '!' or '?' (so any sentence termination), I'd like to be able to send early each sentences so text to speech starts sooner (no need to wait for the whole text to be generated) given less latency to the user when the text is said.