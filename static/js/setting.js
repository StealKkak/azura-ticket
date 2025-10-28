const actionContainer = document.getElementById("actionContainer");
const ticketSelectContainer = document.getElementById("ticketSelectContainer");
const ticketListContainer = document.getElementById("ticketListContainer");
const dashboardContainer = document.getElementById("dashboardContainer");

const addTicketTypeModal = document.getElementById("addTicketTypeModal");

const loadingSpinner = document.getElementById("loadingSpinner");

const pathParts = window.location.pathname.split('/').filter(Boolean);
const guildId = pathParts[pathParts.length - 1];

const dupTicketCheckbox = document.getElementById("dupTicketCheckbox");
const ticketNameInput = document.getElementById("ticketName");
const ticketDescriptInput = document.getElementById("ticketDescription");
const roleListDropdown = document.getElementById("roleListDropdown");
const survey1Checkbox = document.getElementById("surveyCheck1");
const survey2Checkbox = document.getElementById("surveyCheck2");
const survey3Checkbox = document.getElementById("surveyCheck3");
const survey1Input = document.getElementById("survey1Input");
const survey2Input = document.getElementById("survey2Input");
const survey3Input = document.getElementById("survey3Input");
const ticketCategoryList = document.getElementById("ticketCategoryList");
const closedTicketCategoryList = document.getElementById("closedTicketCategoryList");
const ticketCategorySelect = document.getElementById("ticketCategorySelect");
const closedTicketCategorySelect = document.getElementById("closedTicketCategorySelect");
const userCloseCheckbox = document.getElementById("userCloseCheckbox");

const setTicketEmbedModal = document.getElementById("setTicketEmbedModal");
const inputTicketBody = document.getElementById("inputTicketBody");
const inputTicketEmbed = document.getElementById("inputTicketEmbed");

const searchInput = document.getElementById("searchInput");
const searchForm = document.getElementById("searchForm");

let currentTickets = [];

containerList = [actionContainer, ticketListContainer, ticketSelectContainer];
let ticketTypeIndex;

let searchQuery = "";

document.querySelectorAll(".previousButton").forEach(button => {
    button.addEventListener("click", () => {
        containerList.forEach(element => {
            element.classList.add("d-none");
        });
        actionContainer.classList.remove("d-none");
    });
});
document.getElementById("ticketSettingButton").addEventListener("click", async () => {
    actionContainer.classList.add("d-none");
    list = await fetchTicketTypeList();
    renderTicketTypeList(list);
    ticketSelectContainer.classList.remove("d-none");
});

document.getElementById("ticketListButton").addEventListener("click", async () => {
    actionContainer.classList.add("d-none");
    ticketListContainer.classList.remove("d-none");
    showSpinner();
    const ticketList = await fetchTicketList();
    renderPagination(ticketList.current_page, ticketList.total_pages);
    renderTickets(ticketList);
    hideSpinner();
});

function showSpinner() {
    loadingSpinner.classList.add("d-flex")
    loadingSpinner.classList.remove("d-none")
}

function hideSpinner() {
    loadingSpinner.classList.remove("d-flex");
    loadingSpinner.classList.add("d-none");
}

async function fetchTicketTypeList() {
    showSpinner();
    try {
        const res = await fetch(`/api/guilds/${guildId}/ticket-settings`);
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.error || "불러오기 실패");
        }

        return data.data;
    } catch (error) {
        alert(error.message);
    } finally {
        hideSpinner();
    }
}

function renderTicketTypeList(ticketTypeListArray) {
    const ticketTypeList = document.getElementById("ticketTypeList");
    document.getElementById("default-ticket").selected = true;
    ticketTypeList.innerHTML = "";
    ticketTypeListArray.forEach((ticketType, index) => {
        const option = document.createElement("option");
        option.value = index;
        option.textContent = ticketType.name;
        ticketTypeList.appendChild(option);
    });
}

async function fetchTicketList(page = 1, query = "") {
    try {
        let url = `/api/ticket/${guildId}?`;

        if (query) {
            url += `&query=${encodeURIComponent(query)}`;
        }

        if (page) {
            url += `&page=${encodeURIComponent(page)}`
        }

        const response = await fetch(url);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "불러오기 실패");
        }
        
        return data;
    } catch (error) {
        alert(error.message);
        return [];
    }
}

function renderTickets(tickets) {
    if (tickets.data.length === 0) {
        ticketListBody.innerHTML = `<tr><td colspan="3">검색 결과가 없습니다.</td></tr>`;
        return;
    }

    ticketListBody.innerHTML = tickets.data.map(ticket => `
        <tr>
            <td>${ticket.username}</td>
            <td>${ticket.close_time}</td>
            <td>
                <a href="/ticket/${guildId}/${ticket.channel_id}" target="_blank">
                    <button class="btn btn-sm btn-outline-primary">보기</button>
                </a>
            </td>
        </tr>
    `).join("");
}

function renderPagination(currentPage, totalPages) {
    if (totalPages <= 1) {
        pagination.innerHTML = "";
        return;
    }

    let html = `
        <li class="page-item ${currentPage === 1 ? "disabled" : ""}">
            <button class="page-link" data-page="${currentPage - 1}" aria-label="이전 페이지">
                <span aria-hidden="true">◀</span>
            </button>
        </li>`;

    for (let i = 1; i <= totalPages; i++) {
        html += `
            <li class="page-item ${i === currentPage ? "active" : ""}" aria-current="${i === currentPage ? "page" : undefined}">
                <button class="page-link" data-page="${i}">${i}</button>
            </li>`;
    }

    html += `
        <li class="page-item ${currentPage === totalPages ? "disabled" : ""}">
            <button class="page-link" data-page="${currentPage + 1}" aria-label="다음 페이지">
                <span aria-hidden="true">▶</span>
            </button>
        </li>`;

    pagination.innerHTML = html;

    pagination.querySelectorAll("button").forEach(btn => {
        if (!btn.parentElement.classList.contains("disabled")) {
            btn.addEventListener("click", async () => {
                const selectedPage = Number(btn.dataset.page);
                const tickets = await fetchTicketList(selectedPage, searchQuery);

                renderTickets(tickets);
                renderPagination(tickets.current_page, tickets.total_pages);
                window.scrollTo({ top: 0, behavior: "smooth" });
            });
        }
    });
}

addTicketTypeModal.addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = document.getElementById("inputAddTicketTypeName").value;
    try {
        const res = await fetch(`/api/guilds/${guildId}/ticket-settings`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                "name": name
            })
        });
        const data = await res.json();

        if (!res.ok) {
            Swal.fire({
                "title": "오류",
                "icon": "error",
                "text": data.error || "알 수 없는 오류입니다!",
                "confirmButtonText": "닫기"
            });
            return;
        }
        
        showSpinner();
        list = await fetchTicketTypeList();
        renderTicketTypeList(list);
        Swal.fire({
            "title": "성공",
            "text": "티켓 종류 추가가 완료되었습니다!",
            "icon": "success",
            "confirmButtonText": "닫기"
        });
    } catch (error) {
        alert("오류");
        console.error(error);
    }
});

document.getElementById("ticketTypeSelect").addEventListener("change", async (e) => {
    showSpinner();

    try {
        const res = await fetch(`/api/guilds/${guildId}/roles`);
        const data = await res.json();
        roleListDropdown.innerHTML = "";

        if (res.ok) {
            data.data.forEach(role => {
                const div = document.createElement("div");
                div.className = "form-check";
                div.innerHTML = `
                <input class="form-check-input" type="checkbox" value="${role.id}" id="role-${role.id}">
                <label class="form-check-label" for="role-${role.id}">${role.name}</label>
                `;
                roleListDropdown.appendChild(div);
            });
        } else {
            roleListDropdown.innerHTML = `<option value='' selected disabled>${data.error}</option>`;
        }
    } catch (error) {
        Swal.fire({
            "title": "오류",
            "icon": "error",
            "text": error || "알 수 없는 오류입니다!",
            "confirmButtonText": "닫기"
        });
        return;
    }

    try {
        const res = await fetch(`/api/guilds/${guildId}/channels`);
        const data = await res.json();
        
        ticketCategoryList.innerHTML = "";
        closedTicketCategoryList.innerHTML = ""

        if (res.ok) {
            data.data.forEach(channel => {
                if (channel.type == 4) {
                    const option = document.createElement("option");
                    option.value = channel.id;
                    option.textContent = channel.name;
                    ticketCategoryList.appendChild(option);
                    closedTicketCategoryList.appendChild(option.cloneNode(true));
                }
            });
        } else {
            ticketCategoryList.innerHTML = `<option value='' selected disabled>${data.error}</option>`;
            closedTicketCategoryList.innerHTML = `<option value='' selected disabled>${data.error}</option>`;
        }
    } catch (error) {
        Swal.fire({
            "title": "오류",
            "icon": "error",
            "text": error || "알 수 없는 오류입니다!",
            "confirmButtonText": "닫기"
        });
        return;
    }

    try {
        ticketTypeIndex = e.target.value;
        const res = await fetch(`/api/guilds/${guildId}/ticket-settings/${ticketTypeIndex}`);
        const data = await res.json();

        if (!res.ok) {
            Swal.fire({
                "title": "오류",
                "icon": "error",
                "text": error || "알 수 없는 오류입니다!",
                "confirmButtonText": "닫기"
            });
            return;
        }

        ticketNameInput.value = data.data.name;
        ticketDescriptInput.value = data.data.description;

        dupTicketCheckbox.checked = data.data.dup_ticket;

        survey1Checkbox.checked = Boolean(data.data.survey1);
        survey2Checkbox.checked = Boolean(data.data.survey2);
        survey3Checkbox.checked = Boolean(data.data.survey3);

        survey1Input.value = data.data.survey1;
        survey2Input.value = data.data.survey2;
        survey3Input.value = data.data.survey3;

        userCloseCheckbox.checked = data.data.user_close

        if (Array.from(ticketCategorySelect.options).some(opt => opt.value == data.data.ticket_category)) {
            ticketCategorySelect.value = data.data.ticket_category;
        }

        if (Array.from(closedTicketCategorySelect.options).some(opt => opt.value == data.data.closed_ticket_category)) {
            closedTicketCategorySelect.value = data.data.closed_ticket_category;
        }

        for (let role of data.data.role) {
            const checkbox = document.getElementById(`role-${role}`);
            if (checkbox) {
                checkbox.checked = true;
            }
        }
    } catch (error) {
        console.error(error);
        Swal.fire({
            "title": "오류",
            "icon": "error",
            "text": error || "알 수 없는 오류입니다!",
            "confirmButtonText": "닫기"
        });
        return;
    }

    hideSpinner();
    ticketSelectContainer.classList.add("d-none");
    dashboardContainer.classList.remove("d-none");
});

document.getElementById("globalPreviousButton").addEventListener("click", async (e) => {
    dashboardContainer.classList.add("d-none");
    list = await fetchTicketTypeList();
    renderTicketTypeList(list);
    ticketSelectContainer.classList.remove("d-none");
});

document.getElementById("globalDeleteButton").addEventListener("click", async (e) => {
    const confirm = await Swal.fire({
        title: "티켓을 삭제하시겠습니까?",
        text: "이 티켓은 영원히 삭제됩니다!",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#3085d6",
        cancelButtonColor: "#d33",
        confirmButtonText: "삭제",
        cancelButtonText: "취소"
    });
    if (!confirm.isConfirmed) {
        return;
    }

    const res = await fetch(`/api/guilds/${guildId}/ticket-settings/${ticketTypeIndex}`, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json"
        }
    });
    const data = await res.json();

    if (!res.ok) {
        Swal.fire({
            "title": "오류",
            "icon": "error",
            "text": data.error || "알 수 없는 오류입니다!",
            "confirmButtonText": "닫기"
        });
    } else {
        Swal.fire({
            "title": "성공",
            "text": "티켓 종류 삭제가 완료되었습니다!",
            "icon": "success",
            "confirmButtonText": "닫기"
        });
        dashboardContainer.classList.add("d-none");
        list = await fetchTicketTypeList();
        renderTicketTypeList(list);
        ticketSelectContainer.classList.remove("d-none");
    }
});

document.getElementById("globalSaveButton").addEventListener("click", async (e) => {
    const ticketName = ticketNameInput.value;
    const ticketDescription = ticketDescriptInput.value;

    const dupTicket = dupTicketCheckbox.checked;

    const survey1 = survey1Input.value;
    const survey2 = survey2Input.value;
    const survey3 = survey3Input.value;

    const survey1Checked = survey1Checkbox.checked;
    const survey2Checked = survey2Checkbox.checked;
    const survey3Checked = survey3Checkbox.checked;

    const ticketCategory = document.getElementById("ticketCategorySelect").value;
    const closedTicketCategory = document.getElementById("closedTicketCategorySelect").value;

    const checked = roleListDropdown.querySelectorAll(".form-check-input:checked");
    const roles = Array.from(checked).map(cb => cb.value);

    const userClose = userCloseCheckbox.checked;

    const body = inputTicketBody.value;
    const embed = inputTicketEmbed.value;

    const res = await fetch(`/api/guilds/${guildId}/ticket-settings/${ticketTypeIndex}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        }, 
        body: JSON.stringify({
            name: ticketName,
            description: ticketDescription,
            dup_ticket: dupTicket,
            survey1: survey1Checked ? survey1 : null,
            survey2: survey2Checked ? survey2 : null,
            survey3: survey3Checked ? survey3 : null,
            ticket_category: ticketCategory,
            closed_ticket_category: closedTicketCategory,
            role: roles,
            user_close: userClose,
            body,
            embed
        })
    });
    data = await res.json();

    if (!res.ok) {
        Swal.fire({
            "title": "오류",
            "icon": "error",
            "text": data.error || "알 수 없는 오류입니다!",
            "confirmButtonText": "닫기"
        });
        return;
    }

    Swal.fire({
        "title": "성공",
        "text": "저장이 완료되었습니다!",
        "icon": "success",
        "confirmButtonText": "닫기"
    });
});

searchForm.addEventListener("submit", async (e) => {
    e.preventDefault()
    currentPage = 1;
    searchQuery = searchInput.value.trim();
    showSpinner();
    currentTickets = await fetchTicketList(1, searchQuery);
    renderPagination(currentTickets.current_page, currentTickets.total_pages);
    renderTickets(currentTickets);
    hideSpinner();
});

setTicketEmbedModal.addEventListener("submit", async (e) => {
    e.preventDefault();
})