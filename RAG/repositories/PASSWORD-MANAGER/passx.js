let btn = document.querySelector("#btn");
let form = document.querySelector("#form");
let table = document.querySelector("table");

form.addEventListener("submit", (event) => {
    event.preventDefault();

    let webinputval = document.querySelector("#webinput").value.trim();
    let userinputval = document.querySelector("#userinput").value.trim();
    let passinputval = document.querySelector("#passinput").value.trim();

    if (!webinputval || !userinputval || !passinputval) {
        alert("Please fill all fields.")
        return;
    }

    let newRow = document.createElement("tr");

    newRow.innerHTML = `
    <td style="padding: 10px;">${webinputval}</td>
    <td style="padding: 10px;">${userinputval}</td>
    <td style="padding: 10px;">${passinputval}</td>
    <td style="padding: 10px;"><button class="delbtn">Delete</button></td>
    `

    table.appendChild(newRow);

    document.querySelector("#webinput").value = "";
    document.querySelector("#userinput").value = "";
    document.querySelector("#passinput").value = "";

    let delbtn = newRow.querySelector(".delbtn");

    delbtn.addEventListener("click", () => {

        newRow.remove();
    })
});



