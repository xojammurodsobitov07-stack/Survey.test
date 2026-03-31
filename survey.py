import json
import re
from datetime import datetime

# --- Variable types used for marking criteria ---
survey_title: str = "Extracurricular Activities & Study Stress Survey"
passing_score: float = 40.0
is_saved: bool = False
score_range: range = range(0, 81)
allowed_formats: tuple = ("txt", "csv", "json")
seen_ids: set = set()
frozen_states: frozenset = frozenset(
    ["Balanced", "Mild", "Moderate", "High", "Severe", "Critical"])

# Psychological states: 6 states (within required 5-7)
states: dict = {
    (0,  13): "Fully Balanced — Extracurricular activities have no negative stress impact.",
    (14, 27): "Mildly Stressed — Minor imbalance; self-monitoring is sufficient.",
    (28, 41): "Moderately Stressed — Noticeable pressure; consider adjusting commitments.",
    (42, 55): "Highly Stressed — Significant impact on well-being; stress management advised.",
    (56, 69): "Severely Stressed — Extracurricular activities are heavily disrupting academic life.",
    (70, 80): "Critical Imbalance — Immediate academic counselling and psychological support recommended."
}


def get_questions(filename: str) -> list:
    """Load questions from external JSON file."""
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: '{filename}' not found.")
        return []


def get_psychological_state(total: int) -> str:
    """Return psychological state based on total score."""
    for (low, high), state in states.items():
        if low <= total <= high:
            return state
    return "Unknown state."


def validate_name(prompt: str) -> str:
    """Validate name: only letters, hyphens, apostrophes, spaces."""
    while True:
        name = input(prompt).strip()
        # Use for loop to check each character
        valid = True
        for ch in name:
            if not (ch.isalpha() or ch in "-' "):
                valid = False
                break
        if valid and len(name) > 0:
            return name
        print("  Invalid name. Only letters, hyphens, apostrophes, and spaces allowed.")


def validate_date_of_birth(prompt: str) -> str:
    """Validate date of birth in DD/MM/YYYY format."""
    while True:
        date_of_birth = input(prompt).strip()
        try:
            date_obj = datetime.strptime(date_of_birth, "%d/%m/%Y")
            if date_obj > datetime.now():
                print("  Date of birth cannot be in the future.")
            else:
                return date_of_birth
        except ValueError:
            print("  Invalid date. Please use DD/MM/YYYY format with valid values.")


def student_id(prompt: str) -> str:
    """Validate student ID: digits only."""
    while True:
        sid = input(prompt).strip()
        if sid.isdigit() and len(sid) > 0:
            return sid
        print("  Invalid ID. Student ID must contain digits only.")


def run_survey(questions: list) -> int:
    """Run the questionnaire and return total score."""
    answers: list = []
    total: int = 0
    print("\n" + "=" * 60)
    print("Please answer each question by entering the option number.")
    print("=" * 60 + "\n")

    for i, q in enumerate(questions):
        print(f"Q{i + 1}. {q['question']}")
        for j, option in enumerate(q["options"]):
            print(f"  {j + 1}. {option}")

        # While loop for input validation on each answer
        while True:
            answer = input("  Your answer (enter number): ").strip()
            if answer.isdigit() and 1 <= int(answer) <= len(q["options"]):
                choice = int(answer) - 1
                total += q["scores"][choice]
                answers.append(q["options"][choice])
                break
            else:
                print(
                    f"  Please enter a number between 1 and {len(q['options'])}.")
        print()

    return total


def save_results(data: dict, format: str) -> None:
    """Save results to file in chosen format."""
    filename = f"result_{data['student_id']}.{format}"

    if format == "json":
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

    elif format == "csv":
        with open(filename, "w") as f:
            for key, value in data.items():
                f.write(f"{key},{value}\n")

    elif format == "txt":
        with open(filename, "w") as f:
            for key, value in data.items():
                f.write(f"{key}: {value}\n")

    print(f"\n  Results saved to '{filename}'.")


def load_existing_result() -> None:
    """Load and display an existing result file."""
    filename = input(
        "Enter the filename to load (e.g. result_123456.json): ").strip()
    format = filename.split(".")[-1]

    try:
        if format == "json":
            with open(filename, "r") as f:
                data = json.load(f)
            print("\n--- Loaded Results ---")
            for key, value in data.items():
                print(f"  {key}: {value}")

        elif format in ("csv", "txt"):
            with open(filename, "r") as f:
                print("\n--- Loaded Results ---")
                print(f.read())

        else:
            print("Unsupported file format.")

    except FileNotFoundError:
        print(f"  File '{filename}' not found.")


def main():
    print("\n" + "=" * 60)
    print(f"  {survey_title}")
    print("=" * 60)
    print("\n  1. Start a new survey")
    print("  2. Load existing results from file")

    # Conditional statements
    while True:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        if choice == "1":
            break
        elif choice == "2":
            load_existing_result()
            return
        else:
            print("  Please enter 1 or 2.")

    # Collect and validate user details
    print("\n--- Enter Your Details ---")
    name = validate_name("Full name: ")
    date_of_birth = validate_date_of_birth("Date of birth (DD/MM/YYYY): ")
    student_id = student_id("Student ID: ")
    seen_ids.add(student_id)

    # Load questions from external file
    questions = get_questions("questions.json")
    if not questions:
        return

    # Run the survey
    total = run_survey(questions)
    state = get_psychological_state(total)

    # Display results
    print("=" * 60)
    print(f"  Name        : {name}")
    print(f"  Date of Birth : {date_of_birth}")
    print(f"  Student ID  : {student_id}")
    print(f"  Total Score : {total} / {max(score_range) - 1}")
    print(f"  Result      : {state}")
    print("=" * 60)

    # Ask to save
    save_choice = input(
        "\nWould you like to save your results? (yes/no): ").strip().lower()
    if save_choice == "yes":
        print(f"  Available formats: {', '.join(allowed_formats)}")
        format = input("  Choose format (txt / csv / json): ").strip().lower()
        if format in allowed_formats:
            result_data: dict = {
                "name": name,
                "date_of_birth": date_of_birth,
                "student_id": student_id,
                "total_score": total,
                "psychological_state": state
            }
            save_results(result_data, format)
            is_saved = True
        else:
            print("  Invalid format. Results not saved.")

    print("\nThank you for completing the survey!\n")


main()
