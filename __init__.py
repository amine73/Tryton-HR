# :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
# license: BSD, see LICENSE for more details.
 
from trytond.pool import Pool
from .company import *
from .payroll import *
from .attendance import *
from .configuration import *

      
def register():
    Pool.register(
      Department,
      Employee,
      Responsibility,
      Language,
      Academic,
      Skill,
      Team,
      TransferProposal,
      TransferRemark,
      PayrollYear,
      PayrollPeriod,
      PayrollHoliday,
      AttendanceSummary,
      LeaveApplication,
      PaymentDetail,
      Party,
      Property,
      Date,
      EmployeeConfigStart,
      LeaveConfiguration,
      EmployeeHistory,
      Attendance,
      Rule,
      module='hr', type_='model')
    Pool.register(
        EmployeeConfig,
        module='hr', type_='wizard')      
