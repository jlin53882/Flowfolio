class Course:
    def __init__(self, name, teacher, schedule, notes=""):
        self.name = name
        self.teacher = teacher
        self.schedule = schedule
        self.notes = notes

    def to_dict(self):
        return {
            "name": self.name,
            "teacher": self.teacher,
            "schedule": self.schedule,
            "notes": self.notes
        }

class PracticeRecord:
    def __init__(self, date_str, piece, hours, notes=""):
        self.date = date_str
        self.piece = piece
        self.hours = float(hours)
        self.notes = notes

    def to_dict(self):
        return {
            "date": self.date,
            "piece": self.piece,
            "hours": self.hours,
            "notes": self.notes
        }