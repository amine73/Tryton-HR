# -*- coding: utf-8 -*-
#  Payroll
# :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
# :license: BSD, see LICENSE for more details.
from sql.conditionals import Coalesce, Case
from dateutil.relativedelta import relativedelta
from trytond.model import ModelView, ModelSQL, fields
from trytond.tools import datetime_strftime
from trytond.wizard import Wizard, StateView, StateTransition, StateAction, \
    Button
from trytond.pyson import Eval, If,PYSONEncoder
from trytond.transaction import Transaction
from trytond.pool import Pool
from datetime import date

__all__ = ['PayrollYear', 'PayrollPeriod', 'PayrollHoliday']


STATES = {
    'readonly': Eval('state') == 'close',
}


DEPENDS = ['state']




class PayrollYear(ModelSQL, ModelView):
    'Payroll Year'
    __name__ = 'payroll.year'
    name = fields.Char('Name', required=True, depends=DEPENDS)
    company =fields.Many2One('company.company', 'Company', required=True,
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ], select=True)
    department = fields.Many2One('company.department', 'Department', required=True, select=True,
        domain=[('company', '=', Eval('company'))],states=STATES, depends=['company'])
    start_date = fields.Date('Start Date', required=True, states=STATES,
        domain=[('start_date', '<=', Eval('end_date', None))],
        depends=DEPENDS + ['end_date'], select=True)
    end_date = fields.Date('End Date', required=True, states=STATES,
        domain=[('end_date', '>=', Eval('start_date', None))],
        depends=DEPENDS + ['start_date'], select=True)
    periods = fields.One2Many('payroll.period', 'payroll_year', 'Periods',
            states=STATES, depends=DEPENDS)
    state = fields.Selection([
        ('open', 'Open'),
        ('close', 'Close'),
        ], 'State', readonly=True, required=True)




    @classmethod
    def __setup__(cls):
        super(PayrollYear, cls).__setup__()
        cls._order.insert(0, ('start_date', 'ASC'))
        cls._error_messages.update({'payrollyear_overlaps': 'You can not have 2 payroll years that overlap!',
               'no_Payroll_date': 'No Payroll year defined for "%s".',
               'close_error': ('You can not close Payroll year "%s" until you '
                    'close all previous fiscal years.'),
               'reopen_error': ('You can not reopen Payroll year "%s" until '
                    'you reopen all later Payroll years.'),})
        cls._buttons.update({
                'create_period': {
                    'invisible': ((Eval('state') != 'open')
                        | Eval('periods', [0])),
                    },
                'close': {
                    'invisible': Eval('state') != 'open',
                    },
                'reopen': {
                    'invisible': Eval('state') != 'close',
                    },
                })




    @staticmethod
    def default_state():
        return 'open'

    @staticmethod
    def default_company():
        return Transaction().context.get('company')




    def check_dates(self):
        transaction = Transaction()
        connection = transaction.connection
        transaction.database.lock(connection, self._table)
        cursor = connection.cursor()
        table = self.__table__()
        cursor.execute(*table.select(table.id,
                where=(((table.start_date <= self.start_date)
                        & (table.end_date >= self.start_date))
                    | ((table.start_date <= self.end_date)
                        & (table.end_date >= self.end_date))
                    | ((table.start_date >= self.start_date)
                        & (table.end_date <= self.end_date)))
                & (table.company == self.company.id)
                & (table.id != self.id)))
        second_id = cursor.fetchone()
        if second_id:
            second = self.__class__(second_id[0])
            self.raise_user_error('payrollyear_overlaps', {
                    'first': self.rec_name,
                    'second': second.rec_name,
                    })





    @classmethod
    @ModelView.button
    def close(cls, payrollyears):
        # Close a payroll year
        payrollyear = Pool().get('payroll.year')
        Period = Pool().get('payroll.period')
        i=0
        for payrollyear in payrollyears:
            cls.write(payrollyears, {'state': 'close'})
            while Period in payrollyear.periods:
                cls.write(Period, {'state': 'close'})
                i+=i




    @classmethod
    @ModelView.button
    def reopen(cls, payrollyears):
        # Reopen a payroll year
        cls.write(payrollyears, {'state': 'open'})





    @classmethod
    @ModelView.button
    def create_period(cls, payrollyears, interval=1):
        '''
        Create periods for the payroll years with month interval
        '''
        Period = Pool().get('payroll.period')
        to_create = []
        for payrollyear in payrollyears:
            period_start_date = payrollyear.start_date
            while period_start_date < payrollyear.end_date:
                period_end_date = period_start_date + \
                    relativedelta(months=interval - 1) + \
                    relativedelta(day=31)
                if period_end_date > payrollyear.end_date:
                    period_end_date = payrollyear.end_date
                name = datetime_strftime(period_start_date, '%m-%Y')
                if name != datetime_strftime(period_end_date, '%m-%Y'):
                    name += ' - ' + datetime_strftime(period_end_date, '%m-%Y')
                to_create.append({
                    'name': name,
                    'start_date': period_start_date,
                    'end_date': period_end_date,
                    'department': payrollyear.department.id,
                    'payroll_year': payrollyear.id,
                    'end_date': period_end_date,
                    })
                period_start_date = period_end_date + relativedelta(days=1)
        if to_create:
            Period.create(to_create)






class PayrollPeriod(ModelSQL, ModelView):
    'Payroll Period'
    __name__ = 'payroll.period'
    name = fields.Char('Name', required=True)
    payroll_year = fields.Many2One('payroll.year', 'Year',
        required=True, states=STATES, depends=DEPENDS, select=True)
    department = fields.Many2One('company.department', 'Department', required=True, select=True,states=STATES, depends=DEPENDS)
    start_date = fields.Date('Start Date', required=True, states=STATES,
        domain=[('start_date', '<=', Eval('end_date', None))],
        depends=DEPENDS + ['end_date'], select=True)
    end_date = fields.Date('End Date', required=True, states=STATES,
        domain=[('end_date', '>=', Eval('start_date', None))],
        depends=DEPENDS + ['start_date'], select=True)
    holidays = fields.One2Many('payroll.holiday', 'period', 'Holidays', states=STATES, depends=DEPENDS)
    state = fields.Selection([
        ('open', 'Open'),
        ('close', 'Close'),
        ], 'State', readonly=True, required=True)



    @classmethod
    def __setup__(cls):
        super(PayrollPeriod, cls).__setup__()
        cls._order.insert(0, ('start_date', 'ASC'))
        cls._error_messages.update({'periods_overlaps':
                'You can not have two overlapping periods!',
                'create_period_closed_payrollyear': ('You can not create '
                    'a period on payroll year "%s" because it is closed.'),
                'open_period_closed_payrollyear': ('You can not open period '
                    '"%(period)s" because its payroll year "%(payroll)s" is '
                    'closed.'),
                'close_error': ('You can not close Payroll period "%s" until you '
                    'close all previous Payroll periods.'),
                'Payroll_dates': ('Dates of period "%s" are outside '
                    'are outside it\'s Payroll period dates.'),
                })

        cls._buttons.update({
                'create_period': {
                    'invisible': ((Eval('state') != 'open')
                        | Eval('periods', [0])),
                    },
                'close': {
                    'invisible': Eval('state') != 'open',
                    },
                'reopen': {
                    'invisible': Eval('state') != 'close',
                    },
                })

    @staticmethod
    def default_state():
        return 'open'



    def check_dates(self):
        transaction = Transaction()
        connection = transaction.connection
        transaction.database.lock(connection, self._table)
        table = self.__table__()
        cursor = connection.cursor()
        cursor.execute(*table.select(table.id,
                where=(((table.start_date <= self.start_date)
                        & (table.end_date >= self.start_date))
                        | ((table.start_date <= self.end_date)
                        & (table.end_date >= self.end_date))
                        | ((table.start_date >= self.start_date)
                        & (table.end_date <= self.end_date)))
                        & (table.payroll_year == self.payroll_year.id)
                        & (table.id != self.id)))
        period_id = cursor.fetchone()
        if period_id:
            overlapping_period = self.__class__(period_id[0])
            self.raise_user_error('periods_overlap', {
                    'first': self.rec_name,
                    'second': overlapping_period.rec_name,
                    })


    @classmethod
    def delete(cls, periods):
        cls._check(periods)
        super(Period, cls).delete(periods)

    @classmethod
    @ModelView.button
    def close(cls, periods):
        '''
        Close a payroll period
        '''
        pool = Pool()
        Period = pool.get('payroll.period')
        for Period in periods:
            if cls.search([
                        ('end_date', '<=', Period.start_date),
                        ('state', '=', 'open'),]):
                cls.raise_user_error('close_error', (Period.name,))

            # First close the Payroll to be sure
            # it will not have new period created between.
            cls.write([Period], {
                'state': 'close',
                })




    @classmethod
    @ModelView.button
    def reopen(cls, periods):
        #Reopen a payroll year
        PayrollYear = Pool().get('payroll.year')
        cls.write(periods, {'state': 'open'})
        for period in periods:
            PayrollYear.write([period.payroll_year], {'state': 'open'})



class PayrollHoliday(ModelSQL, ModelView):
    'Payroll Holiday'
    __name__ = 'payroll.holiday'
    period = fields.Many2One('payroll.period', 'Payroll Period', required=True)
    date = fields.Date('Date', required=True, select=True, depends=['period'])




    @classmethod
    def __setup__(cls):
        super(PayrollHoliday, cls).__setup__()
        cls._constraints += [('check_dates', 'wrong_date'),]
        cls._error_messages.update({'wrong_date': 'The date must be between start and end date of period',})

    def check_dates(self):
        transaction = Transaction()
        
        'Check if the date is between start and end date of period'

        if (self.date < self.period.start_date) or (self.date > self.period.end_date):
            self.raise_user_error('wrong_date', (self.rec_name,))
            return False
        return True

