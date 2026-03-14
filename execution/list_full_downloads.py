import os

def list_downloads():
    path = r"c:\Users\su-le\Downloads"
    print(f"Listing files in {path}:")
    for file in os.listdir(path):
        if any(keyword in file for keyword in ["Defiendo", "BD_", "Plan_", "Prompts_", "defiendo", "Motor_"]):
            print(f"- {file}")

if __name__ == "__main__":
    list_downloads()
