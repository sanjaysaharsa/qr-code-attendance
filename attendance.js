const serverURL = "https://qr-code-attendance-eqvu.onrender.com";

function onScanSuccess(decodedText, decodedResult) {
    console.log(`Code matched = ${decodedText}`, decodedResult);
    document.getElementById('qr-reader-results').innerText = decodedText;
    document.getElementById('attendanceStatus').style.display = 'block';

    try {
        const qrData = JSON.parse(decodedText.replace(/'/g, '"')); // Fix JSON format
        console.log("Parsed QR Code Data:", qrData); // Debugging
        const rollNumber = qrData.rollNumber;
        fetchStudentDetails(rollNumber);
    } catch (error) {
        console.error("Error parsing QR code data:", error);
        alert("Invalid QR code data.");
    }
}

function onScanFailure(error) {
    console.warn(`Code scan error = ${error}`);
}

let html5QrcodeScanner = new Html5QrcodeScanner(
    "qr-reader",
    { fps: 10, qrbox: { width: 250, height: 250 } },
    /* verbose= */ false
);

html5QrcodeScanner.render(onScanSuccess, onScanFailure);

async function fetchStudentDetails(rollNumber) {
    try {
        // Retrieve the username from localStorage
        const username = localStorage.getItem("username");
        if (!username) {
            throw new Error("User not logged in.");
        }

        console.log("Username from localStorage:", username); // Debugging

        const response = await fetch(`${serverURL}/student_details/${username}/${rollNumber}`);
        const result = await response.json();

        if (response.ok) {
            displayQRDetails(result.student); // Display student details in the popup
        } else {
            alert(result.error || "Failed to fetch student details.");
        }
    } catch (error) {
        console.error("Error fetching student details:", error);
        alert("Error connecting to server.");
    }
}

function displayQRDetails(student) {
    const popup = document.getElementById('qr-details-popup');
    const content = document.getElementById('qr-details-content');
    content.innerHTML = `
        <p><strong>Roll Number:</strong> ${student.rollNumber}</p>
        <p><strong>Name:</strong> ${student.name}</p>
        <p><strong>Father's Name:</strong> ${student.father_name}</p>
        <p><strong>Mother's Name:</strong> ${student.mother_name}</p>
        <p><strong>Date of Birth:</strong> ${student.date_of_birth}</p>
        <p><strong>Class:</strong> ${student.class}</p>
        <p><strong>Category:</strong> ${student.category}</p>
        <p><strong>Gender:</strong> ${student.gender}</p>
        <p><strong>Academic Year:</strong> ${student.academicYear}</p>
        <button id="submitAttendance">Submit</button>
        <button id="cancelAttendance">Cancel</button>
    `;
    popup.style.display = 'block';

    document.getElementById('submitAttendance').addEventListener('click', async () => {
        await markAttendance(student);
    });

    document.getElementById('cancelAttendance').addEventListener('click', () => {
        closePopup();
    });
}

async function markAttendance(student) {
    const username = localStorage.getItem("username");

    try {
        const attendanceData = {
            username,
            rollNumber: student.rollNumber,
            name: student.name,
            father_name: student.father_name,  // New field
            mother_name: student.mother_name,  // New field
            date_of_birth: student.date_of_birth,  // New field
            class: student.class,
            category: student.category,
            gender: student.gender,
            academicYear: student.academicYear,
            attendance_month: new Date().toLocaleString('default', { month: 'long' }),
            time: new Date().toLocaleTimeString(),
            date: new Date().toLocaleDateString()
        };

        console.log("Sending Attendance Data:", attendanceData);  // Debugging

        const response = await fetch(`${serverURL}/attendance`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(attendanceData)
        });

        const result = await response.json();

        if (response.ok) {
            alert(result.message);
            fetchAttendanceRecords();
            closePopup();
        } else {
            alert(result.error || "Failed to mark attendance.");
        }
    } catch (error) {
        console.error("Error marking attendance:", error);
        alert("Error connecting to server. Please check your network or try again later.");
    }
}
function closePopup() {
    const popup = document.getElementById('qr-details-popup');
    popup.style.display = 'none'; // Hide the popup
}

// Fetch and display attendance records
async function fetchAttendanceRecords() {
    try {
        const username = localStorage.getItem("username");
        if (!username) {
            throw new Error("User not logged in.");
        }

        console.log("Fetching attendance records for username:", username); // Debugging

        const response = await fetch(`${serverURL}/attendance_records/${username}`);
        console.log("Server Response:", response); // Debugging

        if (!response.ok) {
            if (response.status === 404) {
                alert("No attendance records found for this user.");
                return;
            }
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        console.log("Attendance Records:", result); // Debugging

        if (result.records) {
            displayAttendanceRecords(result.records);
        } else {
            alert("No attendance records found.");
        }
    } catch (error) {
        console.error("Error fetching attendance records:", error);
        alert("Error connecting to server. Please check your network or try again later.");
    }
}

function displayAttendanceRecords(records) {
    const recordsContainer = document.getElementById('attendanceRecords');
    recordsContainer.innerHTML = '<h3>Recent Attendance</h3>';

    if (!records || records.length === 0) {
        recordsContainer.innerHTML += '<p>No attendance records found.</p>';
        return;
    }

    const table = document.createElement('table');
    table.innerHTML = `
        <tr>
            <th>Roll Number</th>
            <th>Name</th>
            <th>Class</th>
            <th>Category</th>
            <th>Gender</th>
            <th>Academic Year</th>
            <th>Attendance Month</th>
            <th>Time</th>
            <th>Date</th>
        </tr>
    `;

    records.forEach(record => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${record.rollNumber}</td>
            <td>${record.name}</td>
            <td>${record.class}</td>
            <td>${record.category}</td>
            <td>${record.gender}</td>
            <td>${record.academicYear}</td>
            <td>${record.attendance_month}</td>
            <td>${record.time}</td>
            <td>${record.date}</td>
        `;
        table.appendChild(row);
    });

    recordsContainer.appendChild(table);
}

// Fetch attendance records when the page loads
document.addEventListener('DOMContentLoaded', fetchAttendanceRecords);