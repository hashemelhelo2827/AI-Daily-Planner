from pydantic import BaseModel, Field
from typing import Literal
from datetime import time


WeekDays = Literal[
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


class Habit(BaseModel):
    activity: str = Field(description="name of the activity that u recommend")
    descreption: str=Field (description="illustration of the habit")
    DayOfWeek: list[WeekDays] = Field(description="days to do it in")
    timeinday: time = Field(description="recommended time to do it")


class food(BaseModel):
    name: str = Field(description="name of the food")
    ingrediants: list[str] = Field(
        description="list of the required ingrediants to make this food with wieght , number of pieces or volume"
    )
    DayOfWeek: list[WeekDays] = Field(description="days to do it in")
    timeinday: time = Field(description="recommended time to do it")


class exersizes(BaseModel):
    name: str = Field(description="name of the exercise")
    number: str = Field(
        description='sets and reps in the exact format "SETS x REPS", e.g. "3 x 12". '
        'Always two integers separated by an x. Never add words like "sets", "reps", or "times".'
    )
    DayOfWeek: list[WeekDays] = Field(description="days to do it in")
    timeinday: time = Field(description="recommended time to do it")


class study(BaseModel):
    subject: str = Field(description="name of subject")
    DayOfWeek: list[WeekDays] = Field(description="days to do it in")
    timeinday: time = Field(description="recommended time to do it")


class fun(BaseModel):
    acivity: str = Field(description="name of activity to have fun")
    DayOfWeek: list[WeekDays] = Field(description="days to do it in")
    timeinday: time = Field(description="recommended time to do it")


_food = food
_exersizes = exersizes
_fun = fun


class schedual(BaseModel):
    habit: list[Habit] = Field(description="output list of habbits")
    food: list[_food] = Field(description="output list of food")
    exersizes: list[_exersizes] = Field(description="output list of exersizes")
    studyschedual: list[study] = Field(description="output list of study")
    fun: list[_fun] = Field(description="output list of fun")
