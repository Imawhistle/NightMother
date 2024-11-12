from src.agent.core import NightMother

if __name__ == "__main__":
    print("Starting NightMother...")
    try:
        agent = NightMother()
        agent.start()
    except Exception as e:
        print(f"Error: {e}")