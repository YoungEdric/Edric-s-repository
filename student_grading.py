from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from rich import box
import pyfiglet
import matplotlib.pyplot as plt
import pandas as pd
import os

console = Console()

# ASCII title
title = pyfiglet.figlet_format("🏫 School Dashboard 🏫", font="slant")
console.print(f"[bold magenta]{title}[/]")

# Subjects with emojis
subjects = {
    "Math": "📘", "English": "📖", "Chemistry": "🔬", "Physics": "⚡",
    "History": "🏺", "Geography": "🌍", "Entrepreneurship": "💼",
    "French": "🇫🇷", "Chinese": "🇨🇳"
}

# Input students
students = {}
num_students = int(console.input("[bold cyan]Enter number of students: [/bold cyan]"))

for _ in range(num_students):
    name = console.input("\n[bold yellow]Enter student name: [/bold yellow]")
    marks = {}
    total_score = 0
    for subject in track(subjects, description=f"[green]Collecting {name}'s marks...[/green]"):
        score = int(console.input(f"   ➡️ {subjects[subject]} {subject} score (0-100): "))
        marks[subject] = score
        total_score += score
    percentage = total_score / (len(subjects)*100) * 100
    students[name] = {"marks": marks, "total": total_score, "percentage": percentage}

# Convert to DataFrame for plotting
df = pd.DataFrame({name: data["marks"] for name, data in students.items()}).T
df["Total"] = df.sum(axis=1)
df["Percentage"] = df["Total"] / (len(subjects)*100) * 100

# Ranking
df = df.sort_values("Percentage", ascending=False)
df["Rank"] = range(1, len(df)+1)
df["Status"] = ["✅ Promoted" if p >= df["Percentage"].mean() else "❌ Repeat" for p in df["Percentage"]]

# Grade function
def get_grade(p):
    if p >= 90: return "💎 S"
    elif p >= 80: return "🟢 A"
    elif p >= 70: return "🔵 B"
    elif p >= 60: return "🟡 C"
    elif p >= 50: return "🟠 D"
    else: return "🔴 F"

df["Grade"] = df["Percentage"].apply(get_grade)

# Rich Table
table = Table(title="🏆 Ultra Student Leaderboard 🏆", box=box.DOUBLE_EDGE, header_style="bold white")
table.add_column("Rank", justify="center")
table.add_column("Name", justify="center", style="bold cyan")
for subject, emoji in subjects.items():
    table.add_column(f"{emoji} {subject}", justify="center")
table.add_column("Total", justify="center", style="bold yellow")
table.add_column("Percentage", justify="center", style="green")
table.add_column("Grade", justify="center")
table.add_column("Status", justify="center", style="bold")

# Populate table with top 3 crowns
for idx, row in df.iterrows():
    crown = "👑 " if row["Rank"] == 1 else ("🥈 " if row["Rank"] == 2 else ("🥉 " if row["Rank"] == 3 else ""))
    table.add_row(
        f"{crown}{row['Rank']}", idx,
        *[str(row[sub]) for sub in subjects],
        str(row["Total"]),
        f"{row['Percentage']:.2f}%",
        row["Grade"],
        row["Status"]
    )

console.print(table)

# Class Stats Panel
console.print(Panel.fit(
    f"📊 Class Average: {df['Percentage'].mean():.2f}%\n"
    f"👑 Topper: {df.index[0]} ({df.iloc[0]['Percentage']:.2f}%)\n"
    f"📈 Pass Rate: {(df['Status'] == '✅ Promoted').mean()*100:.2f}%\n"
    f"📉 Lowest: {df.index[-1]} ({df.iloc[-1]['Percentage']:.2f}%)",
    style="bold magenta", title="📈 Class Statistics", border_style="bright_blue"
))

# Subject toppers
topper_panel = "[bold green]🏅 Subject Champions[/bold green]\n"
for subject in subjects:
    topper_name = df[subject].idxmax()
    topper_score = df.loc[topper_name, subject]
    topper_panel += f"• {subjects[subject]} {subject:<15}: [yellow]{topper_name}[/yellow] ({topper_score})\n"
console.print(Panel.fit(topper_panel, border_style="gold3"))

# Plot total scores
plt.figure(figsize=(10,6))
plt.bar(df.index, df["Total"], color="purple")
plt.title("🏆 Total Scores of Students")
plt.ylabel("Total Score")
plt.xlabel("Student")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("student_scores.png")
console.print("📊 Total Scores chart saved as [bold cyan]student_scores.png[/bold cyan]")
