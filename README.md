## Inspiration

We found it difficult to stay on top of our assignments using the plethora of independent study tools on the market. However, among our generation, there is one communication tool that we find ourselves using more than any -- Discord. We decided to create an all-in-one study bot on Discord, so that we can easily stay on top of our assignments without having to download any external software.  

## What it does

StudyBuddy has two main features: a built-in assignment tracker and a Pomodoro-inspired productivity tool. The assignment tracker allows users to input their assignments and due dates, either through a Google Calendar file or manually. The bot will then ping you if any of your outgoing assignment deadlines are approaching. Once you are finished an assignment, you can mark it as "completed" in your calendar.

The Pomodoro productivity tool works by limiting your access to other channels within the server during the "study" period, and re-granting you access during the "break" period. For every 25 minutes of study period, you have 5 minutes of break time. Once your study session is over, you can stop the Pomodoro tool.

## How we built it

Our team used the pycord fork of the discord.py API. 

## Challenges we ran into

One challenge we ran into was parsing the Google Calendar file into a database-friendly object. Another challenge we faced was being able to handle multiple Pomodoro sessions within the same server, and syncing the timers properly between the sessions.

## Accomplishments that we're proud of

We are proud of our teamwork, and how we evenly distributed the workload amongst ourselves and helped each other in the process.

## What we learned

We learned the ins and outs of the pycord library, as well as an introduction to databases through SQLite and asynchronous function calls.

## What's next for StudyBuddy

