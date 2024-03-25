#---------------------------------------------------------------------------------------------
# EVI - DATA - WORKFLOW - TOOLS
# api_evi_data_workflow_tools
#---------------------------------------------------------------------------------------------
import datetime
import logging
import json
import pytz
import locale
from geopy import distance
from dateutil import parser

from shapely.ops import nearest_points
from shapely.geometry import Point, Polygon, LineString



#---------------------------------------------------------------------------------------------
# CLASS ELASTIC_SEARCH
#---------------------------------------------------------------------------------------------
class Toolbox:

    def __init__(self):

        self.evi_language           = 'pt_BR.UTF-8'
        self.evi_timezone           = 'America/Sao_Paulo'
        self.evi_date_format        = '%Y-%m-%dT%H:%M:%S'
        self.evi_fiscal_date_format = '%Y-%m-%d'

    # ----------------------------------------------------------------------------------------------------------
    # FORMAT_FLOAT
    # ----------------------------------------------------------------------------------------------------------
    def format_float( self, arg_valor, arg_decimal = 2 ):
        return 0.00 if not arg_valor else round( float( arg_valor ), arg_decimal )

    # ----------------------------------------------------------------------------------------------------------
    # FORMAT_DATETIME
    # ----------------------------------------------------------------------------------------------------------
    def format_datetime(self, arg_date):
        if arg_date is not None:
            if type(arg_date) is not datetime.datetime:
                try:
                    if 'Z' in arg_date or str(arg_date).count(':') == 3:
                        arg_date = parser.parse(arg_date)
                    else:
                        arg_date = parser.parse(arg_date+"-03:00")
                except Exception:
                    arg_date = parser.parse(arg_date)
        return arg_date

    # ----------------------------------------------------------------------------------------------------------
    # FORMAT_UPPER
    # ----------------------------------------------------------------------------------------------------------
    def format_upper( self, arg_string ):
        return arg_string.upper() if type(arg_string) is str else None

    #---------------------------------------------------------------------------------------------
    # CURRENT_DATE_TIME
    #---------------------------------------------------------------------------------------------
    def current_date_time( self, arg_date_time ):

        if type( arg_date_time ) is not datetime.datetime:
            arg_date_time = self.format_datetime( arg_date_time )

        #locale.setlocale(locale.LC_ALL, self.evi_language)
        current_timezone = pytz.timezone( self.evi_timezone )

        date_time                          = arg_date_time
        date_time_utc                      = date_time.astimezone( current_timezone )
        date_time_utc_string               = date_time_utc.strftime( self.evi_date_format )

        ret_date = {}
        ret_date[ 'utc' ]                  = date_time_utc.strftime("%z")
        ret_date[ 'timezone' ]             = date_time_utc.strftime("%Z")

        ret_date[ 'date_time' ]            = date_time
        ret_date[ 'date_time_utc' ]        = date_time_utc
        ret_date[ 'date_time_utc_string' ] = date_time_utc_string
        ret_date[ 'fiscal_date' ]          = date_time.strftime(self.evi_fiscal_date_format)        
        ret_date[ 'date' ]                 = date_time.strftime("%x")
        ret_date[ 'time' ]                 = date_time.strftime("%X")
        ret_date[ 'am_pm' ]                = date_time.strftime("%p")
        ret_date[ 'day' ]                  = date_time.strftime("%d")
        ret_date[ 'month' ]                = date_time.strftime("%m")
        ret_date[ 'year' ]                 = date_time.strftime("%Y")
        ret_date[ 'week_day' ]             = date_time.strftime("%A").title()
        ret_date[ 'month_name' ]           = date_time.strftime("%B").title()
        ret_date[ 'day_number' ]           = date_time.strftime("%j")
        ret_date[ 'week_number' ]          = date_time.strftime("%U")
        ret_date[ 'quarter' ]              = str( (( int( date_time.strftime("%m") ) -1 ) // 3 + 1 ) )

        return ret_date

    # ----------------------------------------------------------------------------------------------------------
    # CALCULA_DIFF_DATA
    # ----------------------------------------------------------------------------------------------------------
    def calcula_diff_data( self, arg_current_date, arg_start_date ):

        # ----------------------------------------------------------------------------------------------------------
        # CALCULA TEMPO NA CERCA
        # ----------------------------------------------------------------------------------------------------------
        tmp_dif_time = None

        if arg_current_date is not None:

            if arg_start_date is not None:

                tmp_dif_time = arg_current_date - arg_start_date

        if tmp_dif_time:

            tmp_dif_dias = tmp_dif_time.days * 1440      # transforma dias em minutos
            tmp_dif_minutos = tmp_dif_time.seconds / 60  # transforma os segundos em minutos

            tmp_total_dif_time = tmp_dif_dias + tmp_dif_minutos
        else:
            tmp_total_dif_time = 0.00

        return tmp_total_dif_time

class MapTools:

    def __init__(self, evi_tools):
        self.evi_tools = evi_tools

    def split_list(self, a, n):
        k, m = divmod(len(a), n)
        return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


def load_json(arg_json) -> dict:
    return json.loads(arg_json) if type(arg_json) is str else arg_json