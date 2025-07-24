# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################
import logging
import time
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError,UserError
_logger = logging.getLogger(__name__)

class sv_res_company(models.Model):
    _inherit=['res.company']
    
    gps_url = fields.Char("URL (gps)")
    gps_hash = fields.Char("Hash")
    