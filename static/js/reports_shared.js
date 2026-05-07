(function () {
    const toDisplayText = (value, fallback = "-") => {
        const trimmedValue = String(value == null ? "" : value).trim();
        return trimmedValue ? trimmedValue : fallback;
    };

    const escapeHtml = (value) => {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\"/g, "&quot;")
            .replace(/'/g, "&#39;");
    };

    const toColumnLabel = (column) => {
        if (typeof column === "string") {
            return column;
        }

        if (column && typeof column === "object") {
            return String(column.label || column.key || "");
        }

        return "";
    };

    const buildReportSheetHtml = (options) => {
        const settings = options && typeof options === "object" ? options : {};
        const meta = settings.meta && typeof settings.meta === "object" ? settings.meta : {};
        const table = settings.table && typeof settings.table === "object" ? settings.table : {};
        const client = settings.client && typeof settings.client === "object" ? settings.client : {};

        const reportTitle = toDisplayText(settings.reportTitle, "SafeBooks Client Report Sheet");
        const reportSubtitle = toDisplayText(settings.reportSubtitle, "Client-facing format for quick review and print handover");

        const reportTypeLabel = toDisplayText(meta.reportTypeLabel, "Client Report");
        const dateRangeLabel = toDisplayText(meta.dateRangeLabel, "-");
        const generatedLabel = toDisplayText(meta.generatedLabel, "-");

        const clientName = toDisplayText(client.clientName || client.client_name, "Selected client");
        const clientTin = toDisplayText(client.tin || client.tin_number);
        const tradeName = toDisplayText(client.tradeName || client.trade_name);
        const location = toDisplayText(client.location);
        const permitNumber = toDisplayText(client.permitNumber || client.permit_number);
        const birthday = toDisplayText(client.birthday);
        const email = toDisplayText(client.email);

        const rawColumns = Array.isArray(table.columns) ? table.columns : [];
        const columns = rawColumns
            .map((column) => toColumnLabel(column))
            .filter((label) => Boolean(String(label || "").trim()));
        const finalColumns = columns.length ? columns : ["Details"];

        const rows = Array.isArray(table.rows) ? table.rows : [];
        const minRows = Number.isFinite(table.minRows) ? table.minRows : 14;
        const rowCount = Math.max(minRows, rows.length);

        const headerMarkup = finalColumns
            .map((label) => `<th>${escapeHtml(toDisplayText(label, "VALUE"))}</th>`)
            .join("");

        const rowsMarkup = Array.from({ length: rowCount }, (_, rowIndex) => {
            const row = rows[rowIndex];
            if (!row) {
                return `
                    <tr>
                        ${finalColumns.map(() => "<td>&nbsp;</td>").join("")}
                    </tr>
                `;
            }

            const rowCells = Array.isArray(row) ? row : finalColumns.map((column) => row[column]);
            const cellsMarkup = finalColumns
                .map((_, columnIndex) => {
                    return `<td>${escapeHtml(toDisplayText(rowCells[columnIndex], "-"))}</td>`;
                })
                .join("");

            return `
                <tr>
                    ${cellsMarkup}
                </tr>
            `;
        }).join("");

        const rowHint = toDisplayText(settings.rowHint, "Prepared from generated report values.");

        return `
            <h3 class="reports-ledger-title">${escapeHtml(reportTitle)}</h3>
            <p class="reports-ledger-subtitle">${escapeHtml(reportSubtitle)}</p>

            <div class="reports-ledger-meta-row">
                <span class="reports-ledger-meta-pill">Type: ${escapeHtml(reportTypeLabel)}</span>
                <span class="reports-ledger-meta-pill">Range: ${escapeHtml(dateRangeLabel)}</span>
                <span class="reports-ledger-meta-pill">Generated: ${escapeHtml(generatedLabel)}</span>
            </div>

            <table class="reports-ledger-client-table" aria-label="Client details">
                <tbody>
                    <tr>
                        <th>TIN</th>
                        <td>${escapeHtml(clientTin)}</td>
                        <th>Trade Name</th>
                        <td>${escapeHtml(tradeName)}</td>
                    </tr>
                    <tr>
                        <th>Taxpayer</th>
                        <td>${escapeHtml(clientName)}</td>
                        <th>Location</th>
                        <td>${escapeHtml(location)}</td>
                    </tr>
                    <tr>
                        <th>Permit No.</th>
                        <td>${escapeHtml(permitNumber)}</td>
                        <th>Birthday</th>
                        <td>${escapeHtml(birthday)}</td>
                    </tr>
                    <tr>
                        <th>Email</th>
                        <td colspan="3">${escapeHtml(email)}</td>
                    </tr>
                </tbody>
            </table>

            <div class="reports-ledger-grid-wrap">
                <table class="reports-ledger-grid-table" aria-label="Ledger entries">
                    <thead>
                        <tr>
                            ${headerMarkup}
                        </tr>
                    </thead>
                    <tbody>
                        ${rowsMarkup}
                    </tbody>
                </table>
            </div>

            <p class="reports-ledger-note">${escapeHtml(rowHint)}</p>
        `;
    };

    window.SafeBooksReportsShared = {
        buildReportSheetHtml,
    };
})();
