from graph import graph

if __name__ == "__main__":
    while(True):
        user_input = input("我:")
        if user_input == "exit":
            break
        state = graph.invoke({"question": user_input, "messages": [("user", user_input)]})
        print("\nAI: " + state["answer"])