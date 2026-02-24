document.addEventListener("click", function (e) { // lyssnar på alla klick i dokumentet. e är ett eventobjekt som innehåller info om klicket.
            const row = e.target.closest(".clickable-row"); // e.target är det element som blev klickat. closest() letar uppåt i DOM-trädet efter närmsta förälder som matchar selektorn.
            if (!row) return; // Om klicket inte var inne i en rad, gör inget mer.

            if (e.target.closest("a")) return; // Scriptet ignorerar klick på länkar så att de fungerar som vanligt.

            const href = row.getAttribute("data-href"); // Hämta värdet av data-href-attributet från raden.
            if (href) window.location.href = href; // Om href finns, navigera till den URL:en.
            });


document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("loadMoreBtn");
  const tableBody = document.getElementById("tx-table-body");
  const statusEl = document.getElementById("loadMoreStatus");

  if (!btn || !tableBody) return;

  btn.addEventListener("click", async () => {
    const accountId = btn.dataset.accountId;
    const limit = parseInt(btn.dataset.limit || "20", 10);
    const offset = parseInt(btn.dataset.offset || "0", 10);

    btn.disabled = true;
    statusEl.textContent = "Hämtar fler transaktioner...";

    try {
      const res = await fetch(
        `/api/accounts/${accountId}/transactions?limit=${limit}&offset=${offset}`
      );

      if (!res.ok) throw new Error("Network error");

      const data = await res.json();

      data.items.forEach(tx => {
  const row = document.createElement("tr");

  const formattedDate = tx.date
    ? new Date(tx.date).toLocaleString()
    : "";

  const dateText = tx.date || "";

  row.innerHTML = `
    <td>${tx.id}</td>
    <td>${dateText}</td>
    <td>${tx.type}</td>
    <td>${tx.operation}</td>
    <td class="right">${parseFloat(tx.amount).toFixed(2)}</td>
    <td class="right">${parseFloat(tx.new_balance).toFixed(2)}</td>
  `;

  tableBody.appendChild(row);
});

      btn.dataset.offset = data.next_offset;

      if (!data.has_more) {
        btn.style.display = "none";
        statusEl.textContent = "Inga fler transaktioner.";
      } else {
        statusEl.textContent = "";
        btn.disabled = false;
      }

    } catch (error) {
      statusEl.textContent = "Kunde inte hämta fler transaktioner.";
      btn.disabled = false;
      console.error(error);
    }
  });
});