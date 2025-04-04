import { useEffect, useState } from "react";
import {
  fetchEmployees,
  fetchSchedules,
  fetchRules,
  processScheduleChange,
  translationChange,
  processTextRequest,
  getDBChange,
  updateDBChange,
} from "~/api";
import type {
  Employee,
  Schedule,
  Rules,
  ScheduleWithEmployee,
  ScheduleChangeRequest,
  ScheduleChangeResponse,
  SimpleRequest,
} from "~/types";
import { Button, Modal, Input } from "antd";
import { p } from "node_modules/@react-router/dev/dist/routes-DHIOx0R9";

export function meta() {
  return [
    { title: "Employee Scheduling App" },
    {
      name: "description",
      content: "Employee scheduling application dashboard",
    },
  ];
}
type PageText = {
  headBar: string[];
  info: string[];
  scheduleForm: string[];
  userForm: string[];
};
const page_text: PageText = {
  headBar: ["Employee Scheduling Dashboard"],
  info: [
    "Weekly Schedule",
    "shifts",
    "Today's date",
    "Employees",
    "People",
    "Total staff members",
    "Scheduling Rules",
    "days max",
    "balance target",
  ],
  scheduleForm: ["This Week's Schedule", "DATE", "Employee", "Employee"],
  userForm: ["Schedule Change Request"],
};
export default function Home() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [schedules, setSchedules] = useState<ScheduleWithEmployee[]>([]);
  const [rules, setRules] = useState<Rules | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [changeRequest, setChangeRequest] = useState("");
  const [changeResponse, setChangeResponse] =
    useState<ScheduleChangeResponse | null>(null);
  const [requestLoading, setRequestLoading] = useState(false);

  const [openModal, setOpenModal] = useState<boolean>(false);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [modalText, setModalText] = useState("Content of the modal");

  const [pageText, setPageText] = useState<PageText>(page_text);
  // Get current date and week's Monday and Sunday
  const today = new Date();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [language, setLanguage] = useState("Swedish");
  const [languageConfirmLoading, setLanguageConfirmLoading] = useState(false);
  const showModal = () => {
    setIsModalOpen(true);
  };

  const handleOk = async () => {
    setLanguageConfirmLoading(true)
    const data = await translationChange({
      request_text: language,
      page_text: pageText,
    });
    console.log(data);
    setPageText(data.page_text);
    setLanguageConfirmLoading(false)
    setIsModalOpen(false);
  };

  const handleCancel = () => {
    setIsModalOpen(false);
  };
  const formatDate = (date: Date): string => {
    return date.toISOString().split("T")[0];
  };
  const handleApplyChange = async () => {
    try {
      setConfirmLoading(true);
      await setTimeout(() => {
        setConfirmLoading(false);
        setOpenModal(false);
      }, 2000);
    } catch (error) {}
  };
  const test = async () => {
    const data = await getDBChange({
      request_text: changeRequest,
    });
    console.log(data);
    const schedulesData = await fetchSchedules(formatDate(today));
    console.log("ludun", schedulesData);
    // Combine schedules with employee names
    const schedulesWithNames = schedulesData.map((schedule) => {
      const employee = employees.find(
        (emp) => emp.employee_number === schedule.first_line_support
      );
      return {
        ...schedule,
        employee_name: employee ? employee.name : "Unknown Employee",
      };
    });
    setSchedules(schedulesWithNames);
  };
  const apply = async () => {
    const data = await updateDBChange({
      request_text: changeRequest,
    });
    const schedulesData = await fetchSchedules(formatDate(today));
    console.log("ludun", schedulesData);
    // Combine schedules with employee names
    const schedulesWithNames = schedulesData.map((schedule) => {
      const employee = employees.find(
        (emp) => emp.employee_number === schedule.first_line_support
      );
      return {
        ...schedule,
        employee_name: employee ? employee.name : "Unknown Employee",
      };
    });
    setSchedules(schedulesWithNames);
  };
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);

        // Fetch all data in parallel
        const [employeesData, schedulesData, rulesData] = await Promise.all([
          fetchEmployees(),
          fetchSchedules(formatDate(today)),
          fetchRules(),
        ]);

        setEmployees(employeesData);

        // Combine schedules with employee names
        const schedulesWithNames = schedulesData.map((schedule) => {
          const employee = employeesData.find(
            (emp) => emp.employee_number === schedule.first_line_support
          );
          return {
            ...schedule,
            employee_name: employee ? employee.name : "Unknown Employee",
          };
        });

        setSchedules(schedulesWithNames);
        setRules(rulesData);
      } catch (err) {
        console.error("Error loading data:", err);
        setError("Failed to load data. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);
  const handleModelClick = () => {
    setOpenModal(true);
  };
  const handleChangeRequest = async () => {
    if (!changeRequest.trim()) return;
    try {
      setRequestLoading(true);
      setError(null);

      const request: ScheduleChangeRequest = {
        request_text: changeRequest,
      };

      const response = await processScheduleChange(request);
      setChangeResponse(response);

      setOpenModal(true);

      // If the request was approved and changes were applied, refresh the schedules
      if (
        response.analysis.recommendation === "approve" &&
        response.analysis.changes &&
        response.analysis.changes.length > 0
      ) {
        // Fetch updated schedules
        const schedulesData = await fetchSchedules(formatDate(today));

        // Combine schedules with employee names
        const schedulesWithNames = schedulesData.map((schedule) => {
          const employee = employees.find(
            (emp) => emp.employee_number === schedule.first_line_support
          );
          return {
            ...schedule,
            employee_name: employee ? employee.name : "Unknown Employee",
          };
        });

        setSchedules(schedulesWithNames);
      }
    } catch (err) {
      console.error("Error processing schedule change:", err);
      setError("Failed to process schedule change request.");
    } finally {
      setRequestLoading(false);
    }
  };

  const handleUserTextRequest = async () => {
    if (!changeRequest.trim()) return;

    try {
      setRequestLoading(true);
      setError(null);

      const request: SimpleRequest = {
        request: changeRequest,
      };

      const response = await processTextRequest(request);
      setChangeResponse(response);

      // If the request was approved and changes were applied, refresh the schedules
      if (
        response.analysis.recommendation === "approve" &&
        response.analysis.changes &&
        response.analysis.changes.length > 0
      ) {
        // Fetch updated schedules
        const schedulesData = await fetchSchedules(formatDate(today));

        // Combine schedules with employee names
        const schedulesWithNames = schedulesData.map((schedule) => {
          const employee = employees.find(
            (emp) => emp.employee_number === schedule.first_line_support
          );
          return {
            ...schedule,
            employee_name: employee ? employee.name : "Unknown Employee",
          };
        });

        setSchedules(schedulesWithNames);
      }
    } catch (err) {
      console.error("Error processing schedule change:", err);
      setError("Failed to process schedule change request.");
    } finally {
      setRequestLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-lg font-medium text-gray-700 dark:text-gray-300">
          Loading dashboard data...
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="flex w-full flex-col">
        <header className="bg-white shadow dark:bg-gray-800">
          <div className="mx-auto max-w-7xl px-3 py-3 sm:px-4 lg:px-5">
            <h1 className="text-xl font-bold tracking-tight text-gray-900 dark:text-white">
              {pageText.headBar[0]}
            </h1>
          </div>
        </header>
        <Modal
          title="Translate"
          open={isModalOpen}
          onOk={handleOk}
          onCancel={handleCancel}
          confirmLoading={languageConfirmLoading}
        >
          <Input
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
          ></Input>
        </Modal>
        <Modal
          title="Analysis result"
          open={openModal}
          onOk={handleApplyChange}
          confirmLoading={confirmLoading}
          onCancel={() => setOpenModal(false)}
        >
          <div className="modal-view">
            <div className="mt-4">
              <h2 className="mb-2 text-lg font-semibold text-gray-800 dark:text-gray-200">
                {pageText.scheduleForm[0]}
              </h2>
              <div className="overflow-hidden rounded-lg bg-white shadow dark:bg-gray-800">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th
                        scope="col"
                        className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300"
                      >
                        {pageText.scheduleForm[1]}
                      </th>
                      <th
                        scope="col"
                        className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300"
                      >
                        {pageText.scheduleForm[2]}
                      </th>
                      <th
                        scope="col"
                        className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300"
                      >
                        {pageText.scheduleForm[3] + " ID"}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
                    {schedules.length > 0 ? (
                      schedules.map((schedule) => (
                        <tr key={schedule.date}>
                          <td className="whitespace-nowrap px-3 py-2 text-sm font-medium text-gray-900 dark:text-gray-200">
                            {schedule.date}
                          </td>
                          <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-500 dark:text-gray-300">
                            {schedule.employee_name}
                          </td>
                          <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-500 dark:text-gray-300">
                            {schedule.first_line_support}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td
                          colSpan={3}
                          className="px-3 py-2 text-center text-sm text-gray-500 dark:text-gray-400"
                        >
                          No schedules found for this week
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </Modal>
        <main className="flex-1 p-3">
          {error && (
            <div className="mb-3 rounded-md bg-red-50 p-2 text-red-700 dark:bg-red-900/30 dark:text-red-300">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
            <DashboardCard
              title={pageText.info[0]}
              value={`${schedules.length} ${pageText.info[1]}`}
              description={`${pageText.info[2]}: ${formatDate(today)}`}
              icon="📅"
            />
            <DashboardCard
              title={pageText.info[3]}
              value={employees.length.toString() + ` ${pageText.info[4]}`}
              description={pageText.info[5]}
              icon="👥"
            />
            <DashboardCard
              title={pageText.info[6]}
              value={
                rules ? `${rules.max_days_per_week} ${pageText.info[7]}` : "N/A"
              }
              description={
                rules
                  ? `${rules.preferred_balance * 100}% ${pageText.info[8]}`
                  : "Loading..."
              }
              icon="📏"
            />
          </div>

          <div className="mt-4">
            <h2 className="mb-2 text-lg font-semibold text-gray-800 dark:text-gray-200">
              {pageText.scheduleForm[0]}
            </h2>
            <div className="overflow-hidden rounded-lg bg-white shadow dark:bg-gray-800">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th
                      scope="col"
                      className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300"
                    >
                      {pageText.scheduleForm[1]}
                    </th>
                    <th
                      scope="col"
                      className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300"
                    >
                      {pageText.scheduleForm[2]}
                    </th>
                    <th
                      scope="col"
                      className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300"
                    >
                      {pageText.scheduleForm[3] + " ID"}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
                  {schedules.length > 0 ? (
                    schedules.map((schedule) => (
                      <tr key={schedule.date}>
                        <td className="whitespace-nowrap px-3 py-2 text-sm font-medium text-gray-900 dark:text-gray-200">
                          {schedule.date}
                        </td>
                        <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-500 dark:text-gray-300">
                          {schedule.employee_name}
                        </td>
                        <td className="whitespace-nowrap px-3 py-2 text-sm text-gray-500 dark:text-gray-300">
                          {schedule.first_line_support}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td
                        colSpan={3}
                        className="px-3 py-2 text-center text-sm text-gray-500 dark:text-gray-400"
                      >
                        No schedules found for this week
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="mt-4">
            <h2 className="mb-2 text-lg font-semibold text-gray-800 dark:text-gray-200">
              {pageText.userForm[0]}
            </h2>
            <div className="overflow-hidden rounded-lg bg-white p-3 shadow dark:bg-gray-800">
              <div className="mb-2">
                <textarea
                  id="changeRequest"
                  rows={2}
                  className="mt-1 block w-full rounded-md border border-gray-300 bg-white px-2 py-1 text-sm text-gray-700 shadow-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
                  placeholder="Example: I need to switch my shift on Friday because I have a doctor's appointment."
                  value={changeRequest}
                  onChange={(e) => setChangeRequest(e.target.value)}
                />
              </div>
              <div className="flex space-x-2">
                <button
                  type="button"
                  className="inline-flex justify-center rounded-md border border-transparent bg-indigo-600 px-3 py-1 text-xs font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:ring-offset-1 dark:focus:ring-offset-gray-800"
                  onClick={handleUserTextRequest}
                  //onClick={handleChangeRequest}
                  disabled={requestLoading || !changeRequest.trim()}
                >
                  {requestLoading ? "Processing..." : "Submit Request"}
                </button>

                <Button type="primary" onClick={handleModelClick}>
                  open modal
                </Button>
                <Button type="primary" onClick={() => setIsModalOpen(true)}>
                  translate
                </Button>
                <Button type="primary" onClick={test}>
                  test
                </Button>
                <Button type="primary" onClick={apply}>
                  apply
                </Button>

                {changeResponse && changeResponse.analysis.type === "schedulechange" &&
                  changeResponse.analysis.recommendation === "approve" && (
                    <div className="flex items-center text-xs text-green-600 dark:text-green-400">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="mr-1 h-4 w-4"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                          clipRule="evenodd"
                        />
                      </svg>
                      Schedule changes applied!
                    </div>
                  )}
              </div>
            </div>

            {changeResponse && changeResponse.analysis.type === "schedulechange" && (
              <div className="mt-2 rounded-lg bg-white p-3 shadow dark:bg-gray-800">
                <h3 className="text-base font-medium text-gray-900 dark:text-gray-100">
                  Request Analysis
                </h3>
                <dl className="mt-1 space-y-1">
                  <div className="sm:grid sm:grid-cols-3 sm:gap-2">
                    <dt className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      Reason
                    </dt>
                    <dd className="text-xs text-gray-900 dark:text-gray-300 sm:col-span-2">
                      {changeResponse.analysis.reason || "Not specified"}
                    </dd>
                  </div>
                  <div className="sm:grid sm:grid-cols-3 sm:gap-2">
                    <dt className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      Recommendation
                    </dt>
                    <dd className="text-xs text-gray-900 dark:text-gray-300 sm:col-span-2">
                      <span
                        className={`inline-flex rounded-full px-1.5 text-xs font-semibold
                        ${
                          changeResponse.analysis.recommendation === "approve"
                            ? "bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100"
                            : changeResponse.analysis.recommendation === "deny"
                            ? "bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100"
                            : "bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-100"
                        }`}
                      >
                        {changeResponse.analysis.recommendation.toUpperCase()}
                      </span>
                    </dd>
                  </div>
                  <div className="sm:grid sm:grid-cols-3 sm:gap-2">
                    <dt className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      Changes
                    </dt>
                    <dd className="text-xs text-gray-900 dark:text-gray-300 sm:col-span-2">
                      {changeResponse.analysis.changes &&
                      changeResponse.analysis.changes.length > 0 ? (
                        <ul className="list-inside list-disc">
                          {changeResponse.analysis.changes.map(
                            (change, index) => (
                              <li key={index}>
                                Date: {change.target_date}, Replacement:{" "}
                                {change.suggested_replacement || "None"}
                              </li>
                            )
                          )}
                        </ul>
                      ) : (
                        "No changes specified"
                      )}
                    </dd>
                  </div>
                  <div className="sm:grid sm:grid-cols-3 sm:gap-2">
                    <dt className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      Reasoning
                    </dt>
                    <dd className="text-xs text-gray-900 dark:text-gray-300 sm:col-span-2">
                      {changeResponse.analysis.reasoning}
                    </dd>
                  </div>
                </dl>
              </div>
            )}

            {changeResponse && changeResponse.analysis.type === "schedulechange" && (
              <div className="mt-2 rounded-lg bg-white p-3 shadow dark:bg-gray-800">
                <h3 className="text-base font-medium text-gray-900 dark:text-gray-100">
                  Request Analysis
                </h3>
                <dl className="mt-1 space-y-1">
                  <div className="sm:grid sm:grid-cols-3 sm:gap-2">
                    <dt className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      Reason
                    </dt>
                    <dd className="text-xs text-gray-900 dark:text-gray-300 sm:col-span-2">
                      {changeResponse.analysis.reason || "Not specified"}
                    </dd>
                  </div>
                  <div className="sm:grid sm:grid-cols-3 sm:gap-2">
                    <dt className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      Recommendation
                    </dt>
                    <dd className="text-xs text-gray-900 dark:text-gray-300 sm:col-span-2">
                      <span
                        className={`inline-flex rounded-full px-1.5 text-xs font-semibold
                        ${
                          changeResponse.analysis.recommendation === "approve"
                            ? "bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100"
                            : changeResponse.analysis.recommendation === "deny"
                            ? "bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100"
                            : "bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-100"
                        }`}
                      >
                        {changeResponse.analysis.recommendation.toUpperCase()}
                      </span>
                    </dd>
                  </div>
                  <div className="sm:grid sm:grid-cols-3 sm:gap-2">
                    <dt className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      Changes
                    </dt>
                    <dd className="text-xs text-gray-900 dark:text-gray-300 sm:col-span-2">
                      {changeResponse.analysis.changes &&
                      changeResponse.analysis.changes.length > 0 ? (
                        <ul className="list-inside list-disc">
                          {changeResponse.analysis.changes.map(
                            (change, index) => (
                              <li key={index}>
                                Date: {change.target_date}, Replacement:{" "}
                                {change.suggested_replacement || "None"}
                              </li>
                            )
                          )}
                        </ul>
                      ) : (
                        "No changes specified"
                      )}
                    </dd>
                  </div>
                  <div className="sm:grid sm:grid-cols-3 sm:gap-2">
                    <dt className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      Reasoning
                    </dt>
                    <dd className="text-xs text-gray-900 dark:text-gray-300 sm:col-span-2">
                      {changeResponse.analysis.reasoning}
                    </dd>
                  </div>
                </dl>
              </div>
            )}

          </div>
        </main>
      </div>
    </div>
  );
}

function DashboardCard({ title, value, description, icon }) {
  return (
    <div className="overflow-hidden rounded-lg bg-white shadow dark:bg-gray-800">
      <div className="p-2">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <span className="text-xl">{icon}</span>
          </div>
          <div className="ml-2 w-0 flex-1">
            <dt className="truncate text-xs font-medium text-gray-500 dark:text-gray-400">
              {title}
            </dt>
            <dd>
              <div className="text-base font-semibold text-gray-900 dark:text-white">
                {value}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {description}
              </div>
            </dd>
          </div>
        </div>
      </div>
    </div>
  );
}
