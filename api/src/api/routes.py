from fastapi import APIRouter, Path, Depends, HTTPException, Request
from typing import Annotated, List, Dict, Optional, Union

from opperai import Opper, trace
from .clients.scheduling import SchedulingClient
from .utils import log
from .models import (
    CategorizeResponse, Employee, Schedule, Rules,
    ScheduleChangeRequest, TextQuerryResponse, ScheduleChangeAnalysis,
    MessageResponse, EmployeeCreateRequest, ScheduleCreateRequest, RulesUpdateRequest, SimpleRequest,
    ComplaintResponse, OtherResponse, QuestionResponse,
    CategorizeResponse, Employee, QuestionResponse, Schedule, Rules, PageText,
    ScheduleChangeRequest, ScheduleChangeAnalysis, 
    TranslationChangeRequest, TranslationChangeResponse, TranslateChangeAnalysis,
    MessageResponse, EmployeeCreateRequest, ScheduleCreateRequest, RulesUpdateRequest, SimpleRequest
)

logger = log.get_logger(__name__)

router = APIRouter()

def get_db_handle(request: Request) -> SchedulingClient:
    """Util for getting the Couchbase client from the request state."""
    return request.app.state.db

def get_opper_handle(request: Request) -> Opper:
    """Util for getting the Opper client from the request state."""
    return request.app.state.opper

DbHandle = Annotated[SchedulingClient, Depends(get_db_handle)]
OpperHandle = Annotated[Opper, Depends(get_opper_handle)]

#### Helper Functions ####

@trace
def get_catagory_for_text(
    opper: Opper,
    request_text: str,
) -> CategorizeResponse:
    
    analysis_result, _ = opper.call(
        name="categorize_request",
        instructions="""
        Categorize the given user request into an appropriate category
        """,
        input={
            "request": request_text,
        },
        output_type=CategorizeResponse
    )

    analysis_result.original_query = request_text
    logger.info(f"Category analysis: {analysis_result.dict()}")
    return analysis_result

@trace
def process_schedule_change(
    opper: Opper,
    request_text: str,
    employees: List[Dict],
    current_schedule: List[Dict],
    rules: Dict
) -> ScheduleChangeAnalysis:
    """Process a natural language schedule change request."""
    analysis_result, _ = opper.call(
        name="analyze_schedule_change",
        instructions="""
        Analyze this schedule change request considering the rules and provide a clear recommendation.
        Extract the employee name, target dates, reason for change, and suggest replacements if applicable.
        Use the provided employee and schedule information to make an informed recommendation.
        Consider workload balance, consecutive shifts, and employee absences in your analysis.
        Include the original query text in your analysis.
        """,
        input={
            "request": request_text,
            "employees": employees,
            "current_schedule": current_schedule,
            "rules": rules
        },
        output_type=ScheduleChangeAnalysis
    )

    # Make sure the original query is included in the analysis
    analysis_result.original_query = request_text
    logger.info(f"Schedule change request analysis: {analysis_result.dict()}")
    return analysis_result


@trace
def respond_to_question(
    opper: Opper,
    question: str,
    employees: List[Dict],
    current_schedule: List[Dict],
    rules: Dict
) -> QuestionResponse:
    analysis_result, _ = opper.call(
        name="answer_question",
        instructions="""
        Answer the given question using your own knowledge and the data provided. Use a professional and helpfull tone
        The questions will mainly be about the schedule and emplyees but might cover other topics
        """,
        input={
            "question": question,
            "employees": employees,
            "current_schedule": current_schedule,
            "rules": rules
        },
        output_type=QuestionResponse
    )

    # Make sure the original query is included in the analysis
    analysis_result.original_query = question
    return analysis_result


@trace
def handle_other_type_request(
    opper: Opper,
    request: str,
    employees: List[Dict],
    current_schedule: List[Dict],
    rules: Dict
) -> QuestionResponse:
    analysis_result, _ = opper.call(
        name="handle_other",
        instructions="""
        Try to handle this unknown type of request to the best of your abilities. You can use the provided data or general reasoning
        """,
        input={
            "request": request,
            "employees": employees,
            "current_schedule": current_schedule,
            "rules": rules
        },
        output_type=QuestionResponse
    )

    # Make sure the original query is included in the analysis
    analysis_result.original_query = request
    return analysis_result

@trace
def handle_complaint(
    opper: Opper,
    complaint: str,
    employees: List[Dict],
    current_schedule: List[Dict],
    rules: Dict
) -> QuestionResponse:
    analysis_result, _ = opper.call(
        name="handle_complaint",
        instructions="""
        Handle the complaint of a user of a employee scheduling system
        Use the provided data to gain a deeper understanding of the problem and possible solutions
        Provide a respectfull and understanding response for the user and a solution proposal to be evaluated by a manager or similar
        Do not make any promisses that might not be possible
        """,
        input={
            "complaint": complaint,
            "employees": employees,
            "current_schedule": current_schedule,
            "rules": rules
        },
        output_type=ComplaintResponse
    )
    return analysis_result

    # Make sure the original query is included in the analysis
    analysis_result.original_query = complaint
def process_translate_change(
    opper: Opper,
    request_text: str,
    page_text: PageText 
) -> TranslateChangeAnalysis:
    """Process a natural language schedule change request."""
    analysis_result, _ = opper.call(
        name="translate_change",
        instructions="""
        Translate the list head_bar, info, schedule_form, user_form into request specific language.
        """,
        input={
            "request": request_text,
            "head_bar": page_text.headBar,
            "info": page_text.info,
            "schedule_form": page_text.scheduleForm,
            "user_form": page_text.userForm
        },
        output_type=TranslateChangeAnalysis
    )

    # Make sure the original query is included in the analysis
    analysis_result.request_text = request_text
    logger.info(f"Schedule change request analysis: {analysis_result.dict()}")
    return analysis_result

#### Routes ####

@router.get("", response_model=MessageResponse)
async def hello() -> MessageResponse:
    return MessageResponse(message="Hello from the Employee Scheduling API!")

# Employee Routes
@router.post("/employees", response_model=Employee)
async def create_employee(
    db: DbHandle,
    request: EmployeeCreateRequest
) -> Employee:
    """Create a new employee."""
    employee_id = db.create_employee(
        name=request.name,
        employee_number=request.employee_number,
        known_absences=request.known_absences,
        metadata=request.metadata
    )
    employee = db.get_employee(employee_id)
    return Employee(**employee)

@router.get("/employees", response_model=List[Employee])
async def get_employees(
    db: DbHandle
) -> List[Employee]:
    """Get all employees."""
    employees = db.get_employees()
    return [Employee(**emp) for emp in employees]

@router.get("/employees/{employee_number}", response_model=Employee)
async def get_employee(
    db: DbHandle,
    employee_number: str = Path(..., description="The employee number")
) -> Employee:
    """Get an employee by employee number."""
    employee = db.get_employee(employee_number)
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employee with number {employee_number} not found")
    return Employee(**employee)

@router.put("/employees/{employee_number}", response_model=Employee)
async def update_employee(
    db: DbHandle,
    request: EmployeeCreateRequest,
    employee_number: str = Path(..., description="The employee number")
) -> Employee:
    """Update an employee."""
    # Check if employee exists
    if not db.get_employee(employee_number):
        raise HTTPException(status_code=404, detail=f"Employee with number {employee_number} not found")

    updates = request.dict(exclude_unset=True)
    success = db.update_employee(employee_number, updates)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update employee")

    employee = db.get_employee(employee_number)
    return Employee(**employee)

@router.delete("/employees/{employee_number}", response_model=MessageResponse)
async def delete_employee(
    db: DbHandle,
    employee_number: str = Path(..., description="The employee number")
) -> MessageResponse:
    """Delete an employee."""
    # Check if employee exists
    if not db.get_employee(employee_number):
        raise HTTPException(status_code=404, detail=f"Employee with number {employee_number} not found")

    success = db.delete_employee(employee_number)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete employee")

    return MessageResponse(message=f"Employee {employee_number} deleted successfully")

# Schedule Routes
@router.post("/schedules", response_model=Schedule)
async def create_schedule(
    db: DbHandle,
    request: ScheduleCreateRequest
) -> Schedule:
    """Create a new schedule entry."""
    # Check if employee exists
    if not db.get_employee(request.first_line_support):
        raise HTTPException(status_code=404, detail=f"Employee with number {request.first_line_support} not found")

    date_str = db.create_schedule(
        date_str=request.date,
        employee_number=request.first_line_support
    )

    schedule = db.get_schedule(date_str)
    return Schedule(**schedule)

@router.get("/schedules", response_model=List[Schedule])
async def get_schedules(
    db: DbHandle,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Schedule]:
    """Get schedules within a date range."""
    schedules = db.get_schedules(start_date, end_date)
    return [Schedule(**schedule) for schedule in schedules]

@router.get("/schedules/{date}", response_model=Schedule)
async def get_schedule(
    db: DbHandle,
    date: str = Path(..., description="The date in ISO format (YYYY-MM-DD)")
) -> Schedule:
    """Get a schedule by date."""
    schedule = db.get_schedule(date)
    if not schedule:
        raise HTTPException(status_code=404, detail=f"Schedule for date {date} not found")
    return Schedule(**schedule)

@router.put("/schedules/{date}", response_model=Schedule)
async def update_schedule(
    db: DbHandle,
    request: ScheduleCreateRequest,
    date: str = Path(..., description="The date in ISO format (YYYY-MM-DD)")
) -> Schedule:
    """Update a schedule entry."""
    # Check if schedule exists
    if not db.get_schedule(date):
        raise HTTPException(status_code=404, detail=f"Schedule for date {date} not found")

    # Check if employee exists
    if not db.get_employee(request.first_line_support):
        raise HTTPException(status_code=404, detail=f"Employee with number {request.first_line_support} not found")

    success = db.update_schedule(date, request.first_line_support)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update schedule")

    schedule = db.get_schedule(date)
    return Schedule(**schedule)

@router.delete("/schedules/{date}", response_model=MessageResponse)
async def delete_schedule(
    db: DbHandle,
    date: str = Path(..., description="The date in ISO format (YYYY-MM-DD)")
) -> MessageResponse:
    """Delete a schedule entry."""
    # Check if schedule exists
    if not db.get_schedule(date):
        raise HTTPException(status_code=404, detail=f"Schedule for date {date} not found")

    success = db.delete_schedule(date)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete schedule")

    return MessageResponse(message=f"Schedule for date {date} deleted successfully")

# Rules Routes
@router.get("/rules", response_model=Rules)
async def get_rules(
    db: DbHandle
) -> Rules:
    """Get the scheduling system rules."""
    rules = db.get_rules()
    return Rules(**rules)

@router.put("/rules", response_model=Rules)
async def update_rules(
    db: DbHandle,
    request: RulesUpdateRequest
) -> Rules:
    """Update the scheduling system rules."""
    updates = {k: v for k, v in request.dict().items() if v is not None}

    if not updates:
        raise HTTPException(status_code=400, detail="No valid updates provided")

    success = db.update_rules(updates)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update rules")

    rules = db.get_rules()
    return Rules(**rules)

@router.post("/process-text-request", 
             response_model=TextQuerryResponse) #Union[ScheduleChangeAnalysis, ComplaintResponse, OtherResponse, QuestionResponse])
async def process_text_request(request: SimpleRequest, db: DbHandle, opper: OpperHandle):

    categoryResponse = get_catagory_for_text(opper, request.request)
    category = categoryResponse.category

    if category == "Change schedule":
        return await process_schedule_change_request(
            ScheduleChangeRequest(
                request_text=request.request
            ),
            db, opper
        )

    elif category == "Ask question":

        try:
            employees = db.get_employees()
            formatted_employees = [
                {
                    "name": emp["name"],
                    "employee_number": emp["employee_number"],
                    "first_line_support_count": emp["first_line_support_count"],
                    "known_absences": emp["known_absences"]
                }
                for emp in employees
            ]
        except Exception as e:
            logger.error(f"Error fetching employees: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching employees: {str(e)}")

        # Get all schedules
        try:
            schedules = db.get_schedules()
            formatted_schedules = [
                {
                    "date": schedule["date"],
                    "first_line_support": schedule["first_line_support"]
                }
                for schedule in schedules
            ]
        except Exception as e:
            logger.error(f"Error fetching schedules: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching schedules: {str(e)}")

        # Get rules
        try:
            rules = db.get_rules()
        except Exception as e:
            logger.error(f"Error fetching rules: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching rules: {str(e)}")

        r = respond_to_question(opper, request.request, employees, schedules, rules)
        return TextQuerryResponse(
            request=request.request, 
            analysis=ScheduleChangeAnalysis(
                thoughts=r.thoughts,
                original_query=request.request,
                changes=[],
                reason="Reason " + r.response,
                recommendation="discuss",
                reasoning=r.reasoning
            )
        )

    elif category == "Complaint":
        
        try:
            employees = db.get_employees()
            formatted_employees = [
                {
                    "name": emp["name"],
                    "employee_number": emp["employee_number"],
                    "first_line_support_count": emp["first_line_support_count"],
                    "known_absences": emp["known_absences"]
                }
                for emp in employees
            ]
        except Exception as e:
            logger.error(f"Error fetching employees: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching employees: {str(e)}")

        # Get all schedules
        try:
            schedules = db.get_schedules()
            formatted_schedules = [
                {
                    "date": schedule["date"],
                    "first_line_support": schedule["first_line_support"]
                }
                for schedule in schedules
            ]
        except Exception as e:
            logger.error(f"Error fetching schedules: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching schedules: {str(e)}")

        # Get rules
        try:
            rules = db.get_rules()
        except Exception as e:
            logger.error(f"Error fetching rules: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching rules: {str(e)}")

        r = handle_complaint(opper, request.request, employees, schedules, rules)
        return TextQuerryResponse(
            request=request.request, 
            analysis=ScheduleChangeAnalysis(
                thoughts=r.thoughts,
                original_query=request.request,
                changes=[],
                reason="Reason " + r.user_response + " " + "Solution: " + r.solution_proposal,
                recommendation="discuss",
                reasoning=r.reasoning,
                response = "response-text"
            )
        )

    elif category == "Other":
        try:
            employees = db.get_employees()
            formatted_employees = [
                {
                    "name": emp["name"],
                    "employee_number": emp["employee_number"],
                    "first_line_support_count": emp["first_line_support_count"],
                    "known_absences": emp["known_absences"]
                }
                for emp in employees
            ]
        except Exception as e:
            logger.error(f"Error fetching employees: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching employees: {str(e)}")

        # Get all schedules
        try:
            schedules = db.get_schedules()
            formatted_schedules = [
                {
                    "date": schedule["date"],
                    "first_line_support": schedule["first_line_support"]
                }
                for schedule in schedules
            ]
        except Exception as e:
            logger.error(f"Error fetching schedules: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching schedules: {str(e)}")

        # Get rules
        try:
            rules = db.get_rules()
        except Exception as e:
            logger.error(f"Error fetching rules: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching rules: {str(e)}")

        r = handle_other_type_request(opper, request.request, employees, schedules, rules)
        return TextQuerryResponse(
            request=request.request, 
            analysis=ScheduleChangeAnalysis(
                thoughts=r.thoughts,
                original_query=request.request,
                changes=[],
                reason="Reason " + r.response,
                recommendation="discuss",
                reasoning=r.reasoning
            )
        )


    return TextQuerryResponse(
        request=request.request, 
        analysis=ScheduleChangeAnalysis(
            thoughts="T " + r.category,
            original_query=request.request,
            changes=[],
            reason="Reason " + r.category,
            recommendation="discuss",
            reasoning="reasoning"
        )
    )


# Translate Change Request
@router.post("/translation-changes", response_model=TranslationChangeResponse)
async def process_translate_change_request(
    request: TranslationChangeRequest,
    opper: OpperHandle
) -> TranslationChangeResponse:
     # Process the request
    try:
        analysis = process_translate_change(
            opper,
            request.request_text,
            request.page_text
        )
        logger.info("Completed translate change analysis")
    except Exception as e:
        logger.error(f"Error in translate change analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing translate change: {str(e)}") 
    
    # Construct a PageText object from analysis
    page_text = PageText(
        headBar=analysis.head_bar,
        info=analysis.info,
        scheduleForm=analysis.schedule_form,
        userForm=analysis.user_form
    )
    
    return TranslationChangeResponse(
        request_text=request.request_text,
        page_text= page_text
    )

# Simulate schedule changes without updating the database
# This endpoint simulates the schedule changes based on AI analysis
@router.post("/schedule-changes/simulate", response_model=List[Schedule])
async def simulate_schedule_changes(
    request: ScheduleChangeRequest,
    db: DbHandle,
    opper: OpperHandle
) -> List[Schedule]:
    """Simulate schedule changes based on AI analysis without updating the database."""
    # Get all employees
    try:
        employees = db.get_employees()
        formatted_employees = [
            {
                "name": emp["name"],
                "employee_number": emp["employee_number"],
                "first_line_support_count": emp["first_line_support_count"],
                "known_absences": emp["known_absences"]
            }
            for emp in employees
        ]
    except Exception as e:
        logger.error(f"Error fetching employees: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching employees: {str(e)}")

    # Get all schedules
    try:
        schedules = db.get_schedules()
        simulated_schedules = [
            {
                "date": schedule["date"],
                "first_line_support": schedule["first_line_support"]
            }
            for schedule in schedules
        ]
    except Exception as e:
        logger.error(f"Error fetching schedules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching schedules: {str(e)}")

    # Get rules
    try:
        rules = db.get_rules()
    except Exception as e:
        logger.error(f"Error fetching rules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching rules: {str(e)}")

    # Process the request
    try:
        analysis = process_schedule_change(
            opper,
            request.request_text,
            formatted_employees,
            simulated_schedules,
            rules
        )
        logger.info("Completed schedule change analysis")
    except Exception as e:
        logger.error(f"Error in schedule change analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing schedule change: {str(e)}")

    # Simulate applying changes to the schedule
    for change in analysis.changes:
        target_date = change.target_date
        suggested_replacement = change.suggested_replacement

        # Find the employee number for the suggested replacement
        replacement_employee = next(
            (emp for emp in employees if emp["name"] == suggested_replacement),
            None
        )

        if replacement_employee:
            # Check if the schedule exists for that date
            existing_schedule = next(
                (schedule for schedule in simulated_schedules if schedule["date"] == target_date),
                None
            )

            if existing_schedule:
                # Simulate updating the existing schedule
                existing_schedule["first_line_support"] = replacement_employee["employee_number"]
            else:
                # Simulate creating a new schedule
                simulated_schedules.append({
                    "date": target_date,
                    "first_line_support": replacement_employee["employee_number"]
                })

    # Return the simulated schedules
    return [Schedule(**schedule) for schedule in simulated_schedules]

# Schedule Change Request
@router.post("/schedule-changes", response_model=TextQuerryResponse)
async def process_schedule_change_request(
    request: ScheduleChangeRequest,
    db: DbHandle,
    opper: OpperHandle
) -> TextQuerryResponse:
    """Process a natural language schedule change request."""
    # Get all employees
    try:
        employees = db.get_employees()
        formatted_employees = [
            {
                "name": emp["name"],
                "employee_number": emp["employee_number"],
                "first_line_support_count": emp["first_line_support_count"],
                "known_absences": emp["known_absences"]
            }
            for emp in employees
        ]
    except Exception as e:
        logger.error(f"Error fetching employees: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching employees: {str(e)}")

    # Get all schedules
    try:
        schedules = db.get_schedules()
        formatted_schedules = [
            {
                "date": schedule["date"],
                "first_line_support": schedule["first_line_support"]
            }
            for schedule in schedules
        ]
    except Exception as e:
        logger.error(f"Error fetching schedules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching schedules: {str(e)}")

    # Get rules
    try:
        rules = db.get_rules()
    except Exception as e:
        logger.error(f"Error fetching rules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching rules: {str(e)}")

    # Process the request
    try:
        analysis = process_schedule_change(
            opper,
            request.request_text,
            formatted_employees,
            formatted_schedules,
            rules
        )
        logger.info("Completed schedule change analysis")
    except Exception as e:
        logger.error(f"Error in schedule change analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing schedule change: {str(e)}")

    return TextQuerryResponse(
        request=request.request_text,
        analysis=analysis
    )


@router.post("/schedule-changes/apply", response_model=MessageResponse)
async def apply_schedule_changes(
    request: ScheduleChangeRequest,
    db: DbHandle,
    opper: OpperHandle
) -> MessageResponse:
    """
    Apply schedule changes based on AI recommendations.
    """
    # Get all employees
    try:
        employees = db.get_employees()
        formatted_employees = [
            {
                "name": emp["name"],
                "employee_number": emp["employee_number"],
                "first_line_support_count": emp["first_line_support_count"],
                "known_absences": emp["known_absences"]
            }
            for emp in employees
        ]
    except Exception as e:
        logger.error(f"Error fetching employees: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching employees: {str(e)}")

    # Get all schedules
    try:
        schedules = db.get_schedules()
        formatted_schedules = [
            {
                "date": schedule["date"],
                "first_line_support": schedule["first_line_support"]
            }
            for schedule in schedules
        ]
    except Exception as e:
        logger.error(f"Error fetching schedules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching schedules: {str(e)}")

    # Get rules
    try:
        rules = db.get_rules()
    except Exception as e:
        logger.error(f"Error fetching rules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching rules: {str(e)}")

    # Process the request
    try:
        analysis = process_schedule_change(
            opper,
            request.request_text,
            formatted_employees,
            formatted_schedules,
            rules
        )
        logger.info("Completed schedule change analysis")
    except Exception as e:
        logger.error(f"Error in schedule change analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing schedule change: {str(e)}")

    # Apply changes to the schedule if recommended
    try:
        if analysis.recommendation == "approve":
            for change in analysis.changes:
                target_date = change.target_date
                suggested_replacement = change.suggested_replacement

                # Find the employee number for the suggested replacement
                replacement_employee = next(
                    (emp for emp in employees if emp["name"] == suggested_replacement),
                    None
                )

                if replacement_employee:
                    # Check if the schedule exists for that date
                    existing_schedule = db.get_schedule(target_date)

                    if existing_schedule:
                        # Update the existing schedule
                        success = db.update_schedule(
                            target_date,
                            replacement_employee["employee_number"]
                        )
                        logger.info(
                            f"Schedule change applied: Date {target_date}, "
                            f"New employee: {suggested_replacement}, "
                            f"Success: {success}"
                        )
                    else:
                        # Create a new schedule if it doesn't exist
                        db.create_schedule(
                            target_date,
                            replacement_employee["employee_number"]
                        )
                        logger.info(
                            f"New schedule created: Date {target_date}, "
                            f"Employee: {suggested_replacement}"
                        )
        else:
            logger.info(f"Schedule change recommendation: {analysis.recommendation}")
            return MessageResponse(message=f"Schedule changes not applied. Recommendation: {analysis.recommendation}")
    except Exception as e:
        logger.error(f"Error applying schedule changes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error applying schedule changes: {str(e)}")

    return MessageResponse(message="Schedule changes successfully applied.")
