import pytest
from dashboard.components.database_module import DatabaseModule, SupaBaseApi
import pandas as pd
from datetime import datetime,date
from unittest.mock import patch, Mock

def test_get_current_sesion():
    season = DatabaseModule().get_current_season()
    assert season == "25/26"

def test_parse_role():
    # Test genf role
    assert DatabaseModule().parse_role(birth_year = 2012, season = "25/26") == "genf"
    assert DatabaseModule().parse_role(birth_year = 2010, season = "25/26") == "genf"
    assert DatabaseModule().parse_role(birth_year = 2008, season = "25/26") == "hjelpementor"
    assert DatabaseModule().parse_role(birth_year = 2009, season = "25/26") == "hjelpementor"
    assert DatabaseModule().parse_role(birth_year = 2007, season = "25/26") == "mentor"
    assert DatabaseModule().parse_role(birth_year = 1995, season = "25/26") == "mentor"
    
    # Test mentor role
    assert DatabaseModule().parse_role(birth_year = 2005, season = "25/26") == "mentor"
    assert DatabaseModule().parse_role(birth_year = 1990, season = "25/26") == "mentor"


def test_apply_role():
    assert DatabaseModule().apply_role(birth_date = "2012-05-15", season = "25/26") == "genf"
    assert DatabaseModule().apply_role(birth_date = datetime(2012, 12, 15), season = "25/26") == "genf"
    assert DatabaseModule().apply_role(birth_date = date(2008, 5, 15), season = "25/26") == "hjelpementor"
    assert DatabaseModule().apply_role(birth_date = "2007-01-15", season = None) == "mentor"
    assert DatabaseModule().apply_role(birth_date = date(2013, 11, 2), season = "25/26") == "u13"

def test_mk_gruppe():
    assert DatabaseModule().mk_gruppe("glenne_vedpakking") == "glenne"
    assert DatabaseModule().mk_gruppe("arvoll_kafe_og_vedpakking") == "arvoll"
    assert DatabaseModule().mk_gruppe("glenne") == "glenne"

def test_mk_prosjekt():
    assert DatabaseModule().mk_prosjekt("glenne_vedpakking") == "vedpakking"
    assert DatabaseModule().mk_prosjekt("arvoll_kafe_og_vedpakking") == "kafe og vedpakking"
    assert DatabaseModule().mk_prosjekt("glenne") == "glenne"

def test_apply_cost():
    rates = [{"genf": 100, "hjelpementor": 150, "mentor": 200, "vedsekk": 20, "season": "25/26"},
             {"genf": 90, "hjelpementor": 140, "mentor": 190, "vedsekk": 15, "season": "24/25"}]
    row = pd.Series({"work_type": "glenne_vedpakking", "hours_worked": 5, "units_completed" : 10, "role" : "genf", "season": "25/26"})
    assert DatabaseModule().apply_cost(row, rates) == 20*10

    row = pd.Series({"work_type": "glenne_vedpakking", "hours_worked": 5, "units_completed" : 70, "role" : "mentor", "season": "24/25"})
    assert DatabaseModule().apply_cost(row, rates) == 5 * 190

    row = pd.Series({"work_type": "glenne_vedpakking", "hours_worked": 5, "units_completed" : 15, "role" : "hjelpementor", "season": "25/26"})
    assert DatabaseModule().apply_cost(row, rates) == 5 * 150

    row = pd.Series({"work_type": "bccof_vask", "hours_worked": 10, "units_completed" : None, "role" : "genf", "season": "25/26"})
    assert DatabaseModule().apply_cost(row, rates) == 100*10

    row = pd.Series({"work_type": "bccof_vask", "hours_worked": 10, "units_completed" : None, "role" : "mentor", "season": "25/26"})
    assert DatabaseModule().apply_cost(row, rates) == 200*10

    row = pd.Series({"work_type": "bccof_vask", "hours_worked": 10, "units_completed" : None, "role" : "hjelpementor", "season": "25/26"})
    assert DatabaseModule().apply_cost(row, rates) == 150*10



