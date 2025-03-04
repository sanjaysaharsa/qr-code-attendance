const serverURL = "https://qr-code-attendance-eqvu.onrender.com";

async function registerStudent() {
    try {
        const username = localStorage.getItem("username");
        if (!username) {
            throw new Error("User not logged in.");
        }

        const name = document.getElementById('name').value;
        const rollNumber = document.getElementById('rollNumber').value;
        const father_name = document.getElementById('father_name').value;
        const mother_name = document.getElementById('mother_name').value;
        const date_of_birth = document.getElementById('date_of_birth').value;
        const category = document.getElementById('category').value;
        const gender = document.getElementById('gender').value;
        const classValue = document.getElementById('class').value;
        const academicYear = document.getElementById('academicYear').value;

        const studentData = {
            username,
            rollNumber,
            name,
            father_name,
            mother_name,
            date_of_birth,
            category,
            gender,
            class: classValue,
            academicYear
        };

        console.log("Sending payload:", studentData);

        const response = await fetch(`${serverURL}/register_student`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(studentData)
        });

        const result = await response.json();
        if (response.ok) {
            alert(result.message);
            window.location.href = `student_details.html?username=${username}&rollNumber=${rollNumber}`;
        } else {
            alert(result.error || "Failed to register student.");
        }
    } catch (error) {
        console.error("Error registering student:", error);
        alert("Error connecting to server.");
    }
}