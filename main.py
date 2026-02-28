from graph import graph

if __name__ == "__main__":
    while(True):
        user_input = input("我:")
        if user_input == "exit":
            break
        for stream_mode, chunk in graph.stream(
            input={"question": user_input, "messages": [("user", user_input)]},
            stream_mode=["custom", "updates"]
        ):
            if stream_mode == "custom":
                print(chunk["content"], end="", flush=True)