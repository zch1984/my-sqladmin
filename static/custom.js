// SQLAdmin 自定义JavaScript

document.addEventListener("DOMContentLoaded", function () {
  // 初始化所有功能
  initializeTooltips();
  initializeTableFeatures();
  initializeFormValidation();
  initializeJsonFields();
  addFadeInAnimation();

  console.log("SQLAdmin 自定义脚本已加载");
});

// 初始化工具提示
function initializeTooltips() {
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
}

// 初始化表格功能
function initializeTableFeatures() {
  // 表格行悬停效果
  const tableRows = document.querySelectorAll(".table tbody tr");
  tableRows.forEach((row) => {
    row.addEventListener("mouseenter", function () {
      this.style.backgroundColor = "rgba(37, 99, 235, 0.05)";
    });

    row.addEventListener("mouseleave", function () {
      this.style.backgroundColor = "";
    });
  });

  // 全选功能
  const selectAllCheckbox = document.querySelector("#select-all");
  if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener("change", function () {
      const checkboxes = document.querySelectorAll(".row-checkbox");
      checkboxes.forEach((checkbox) => {
        checkbox.checked = this.checked;
      });
      updateBulkActions();
    });
  }

  // 单选框变化时更新批量操作按钮
  const rowCheckboxes = document.querySelectorAll(".row-checkbox");
  rowCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", updateBulkActions);
  });
}

// 更新批量操作按钮状态
function updateBulkActions() {
  const checkedBoxes = document.querySelectorAll(".row-checkbox:checked");
  const bulkActionBtn = document.querySelector("#bulk-actions-btn");

  if (bulkActionBtn) {
    if (checkedBoxes.length > 0) {
      bulkActionBtn.style.display = "inline-block";
      bulkActionBtn.textContent = `批量操作 (${checkedBoxes.length})`;
    } else {
      bulkActionBtn.style.display = "none";
    }
  }
}

// 初始化表单验证
function initializeFormValidation() {
  const forms = document.querySelectorAll(".needs-validation");

  forms.forEach((form) => {
    form.addEventListener("submit", function (event) {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
    });
  });

  // 实时验证
  const inputs = document.querySelectorAll("input, textarea, select");
  inputs.forEach((input) => {
    input.addEventListener("blur", function () {
      validateField(this);
    });

    input.addEventListener("input", function () {
      if (this.classList.contains("is-invalid")) {
        validateField(this);
      }
    });
  });
}

// 字段验证
function validateField(field) {
  const isValid = field.checkValidity();

  if (isValid) {
    field.classList.remove("is-invalid");
    field.classList.add("is-valid");
  } else {
    field.classList.remove("is-valid");
    field.classList.add("is-invalid");
  }
}

// 初始化JSON字段
function initializeJsonFields() {
  const jsonFields = document.querySelectorAll(".json-field");

  jsonFields.forEach((field) => {
    // 添加JSON格式化按钮
    const formatBtn = document.createElement("button");
    formatBtn.type = "button";
    formatBtn.className = "btn btn-sm btn-outline-secondary mt-2";
    formatBtn.innerHTML = '<i class="fas fa-code"></i> 格式化JSON';
    formatBtn.addEventListener("click", function () {
      formatJsonField(field);
    });

    field.parentNode.appendChild(formatBtn);

    // 添加JSON验证
    field.addEventListener("blur", function () {
      validateJsonField(this);
    });
  });
}

// 格式化JSON字段
function formatJsonField(field) {
  try {
    const jsonValue = JSON.parse(field.value);
    field.value = JSON.stringify(jsonValue, null, 2);
    field.classList.remove("is-invalid");
    field.classList.add("is-valid");

    showNotification("JSON格式化成功", "success");
  } catch (error) {
    showNotification("JSON格式错误: " + error.message, "error");
    field.classList.add("is-invalid");
  }
}

// 验证JSON字段
function validateJsonField(field) {
  if (!field.value.trim()) {
    field.classList.remove("is-invalid", "is-valid");
    return;
  }

  try {
    JSON.parse(field.value);
    field.classList.remove("is-invalid");
    field.classList.add("is-valid");
  } catch (error) {
    field.classList.remove("is-valid");
    field.classList.add("is-invalid");

    // 显示错误提示
    let errorDiv = field.parentNode.querySelector(".json-error");
    if (!errorDiv) {
      errorDiv = document.createElement("div");
      errorDiv.className = "json-error text-danger small mt-1";
      field.parentNode.appendChild(errorDiv);
    }
    errorDiv.textContent = "JSON格式错误: " + error.message;
  }
}

// 添加淡入动画
function addFadeInAnimation() {
  const elements = document.querySelectorAll(".card, .table, .form-group");

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("fade-in");
      }
    });
  });

  elements.forEach((element) => {
    observer.observe(element);
  });
}

// 显示通知
function showNotification(message, type = "info") {
  const notification = document.createElement("div");
  notification.className = `alert alert-${
    type === "error" ? "danger" : type
  } alert-dismissible fade show notification`;
  notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        border-radius: 8px;
    `;

  notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

  document.body.appendChild(notification);

  // 自动消失
  setTimeout(() => {
    if (notification.parentNode) {
      notification.remove();
    }
  }, 5000);
}

// 确认删除操作
function confirmDelete(url, itemName) {
  if (confirm(`确定要删除 "${itemName}" 吗？此操作不可撤销。`)) {
    window.location.href = url;
  }
}

// 批量删除确认
function confirmBulkDelete() {
  const checkedBoxes = document.querySelectorAll(".row-checkbox:checked");
  if (checkedBoxes.length === 0) {
    showNotification("请选择要删除的项目", "warning");
    return false;
  }

  return confirm(
    `确定要删除选中的 ${checkedBoxes.length} 个项目吗？此操作不可撤销。`
  );
}

// 导出数据
function exportData(format = "csv") {
  const checkedBoxes = document.querySelectorAll(".row-checkbox:checked");
  const ids = Array.from(checkedBoxes).map((cb) => cb.value);

  if (ids.length === 0) {
    showNotification("请选择要导出的数据", "warning");
    return;
  }

  // 构建导出URL
  const currentUrl = new URL(window.location);
  currentUrl.searchParams.set("export", format);
  currentUrl.searchParams.set("ids", ids.join(","));

  window.open(currentUrl.toString(), "_blank");
}

// 搜索功能增强
function enhanceSearch() {
  const searchInput = document.querySelector('input[name="search"]');
  if (searchInput) {
    let searchTimeout;

    searchInput.addEventListener("input", function () {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        if (this.value.length >= 2 || this.value.length === 0) {
          this.form.submit();
        }
      }, 500);
    });
  }
}

// 页面加载完成后执行增强功能
window.addEventListener("load", function () {
  enhanceSearch();

  // 添加键盘快捷键
  document.addEventListener("keydown", function (e) {
    // Ctrl+S 保存表单
    if (e.ctrlKey && e.key === "s") {
      e.preventDefault();
      const submitBtn = document.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.click();
      }
    }

    // Escape 关闭模态框
    if (e.key === "Escape") {
      const modals = document.querySelectorAll(".modal.show");
      modals.forEach((modal) => {
        const modalInstance = bootstrap.Modal.getInstance(modal);
        if (modalInstance) {
          modalInstance.hide();
        }
      });
    }
  });
});

// 主题切换功能
function toggleTheme() {
  const body = document.body;
  const isDark = body.classList.contains("dark-theme");

  if (isDark) {
    body.classList.remove("dark-theme");
    localStorage.setItem("theme", "light");
  } else {
    body.classList.add("dark-theme");
    localStorage.setItem("theme", "dark");
  }
}

// 加载保存的主题
function loadTheme() {
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "dark") {
    document.body.classList.add("dark-theme");
  }
}

// 页面加载时应用主题
document.addEventListener("DOMContentLoaded", loadTheme);
