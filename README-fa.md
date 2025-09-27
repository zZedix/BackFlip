# 🚀 Backflip Tunnel

<div align="center">

![Backflip Logo](https://img.shields.io/badge/Backflip-Tunnel-blue?style=for-the-badge&logo=python)

**یک سرویس تانل SSH قدرتمند و مقاوم برای اتصال بین سرورهای ایرانی و خارجی**

[![Python](https://img.shields.io/badge/Python-3.10+-green?style=flat-square&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![SSH](https://img.shields.io/badge/SSH-Tunnel-orange?style=flat-square&logo=ssh)](https://openssh.org)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-20.04+-blue?style=flat-square&logo=ubuntu)](https://ubuntu.com)
[![Debian](https://img.shields.io/badge/Debian-11+-red?style=flat-square&logo=debian)](https://debian.org)

</div>

---

## ✨ ویژگی‌های کلیدی

- 🎯 **نصب آسان**: نصبگر تعاملی با راهنمای کامل
- 🔄 **دو حالت تانل**: مستقیم (`-L`) و معکوس (`-R`)
- ⚡ **اتصال مقاوم**: استفاده از `autossh` با SSH multiplexing
- 🛠️ **مدیریت ساده**: CLI مدیریت برای مشاهده لاگ، راه‌اندازی مجدد و تنظیمات
- 📝 **پیکربندی YAML**: ذخیره تنظیمات در `/etc/backflip/config.yaml`
- 🔧 **سرویس systemd**: راه‌اندازی خودکار و مدیریت سرویس
- 📊 **لاگ‌گیری ساختاریافته**: لاگ‌ها در `/var/log/backflip/` و systemd journal
- 🔐 **پشتیبانی از کلید SSH**: احراز هویت امن بدون رمز عبور
- 🌐 **چند پلتفرمه**: کار روی Ubuntu، Debian و سایر توزیع‌های لینوکس

## 🚀 شروع سریع

### 🎯 نصب یک خطی (پیشنهادی)

```bash
curl -sSfL https://raw.githubusercontent.com/zZedix/BackFlip/main/install.sh | sudo bash
```

**این دستور چه کاری انجام می‌دهد:**
- ✅ وابستگی‌های سیستم را نصب می‌کند (`python3`, `pip`, `autossh`, `openssh-client`)
- ✅ محیط مجازی Python در `/opt/backflip` ایجاد می‌کند
- ✅ آخرین نسخه Backflip را از GitHub دانلود می‌کند
- ✅ جادوگر پیکربندی تعاملی را اجرا می‌کند
- ✅ سرویس systemd را برای راه‌اندازی خودکار تنظیم می‌کند

> 💡 **نصب محلی**: اگر مخزن را به صورت محلی کلون کرده‌اید، از ریشه پروژه دستور `sudo bash install.sh` را اجرا کنید.

### 🔧 نصب دستی

#### مرحله ۱: نصب وابستگی‌های سیستم

**برای Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv autossh openssh-client
```

**برای CentOS/RHEL/Fedora:**
```bash
# CentOS/RHEL
sudo yum install -y python3 python3-pip autossh openssh-clients

# Fedora
sudo dnf install -y python3 python3-pip autossh openssh-clients
```

**برای Arch Linux:**
```bash
sudo pacman -S python python-pip autossh openssh
```

#### مرحله ۲: نصب Backflip

**گزینه الف: از GitHub (پیشنهادی)**
```bash
sudo pip3 install git+https://github.com/zZedix/BackFlip.git
```

**گزینه ب: از منبع محلی**
```bash
git clone https://github.com/zZedix/BackFlip.git
cd BackFlip
sudo pip3 install .
```

#### مرحله ۳: اجرای جادوگر پیکربندی

```bash
sudo backflip-install
```

جادوگر این کارها را انجام می‌دهد:
- ✅ وابستگی‌های مورد نیاز را بررسی می‌کند
- ✅ حالت تانل (مستقیم/معکوس) را می‌پرسد
- ✅ آدرس سرورها را می‌پرسد
- ✅ نگاشت‌های پروکسی را پیکربندی می‌کند
- ✅ SSH multiplexing را تنظیم می‌کند
- ✅ سرویس systemd را ایجاد می‌کند
- ✅ سرویس را فعال و راه‌اندازی می‌کند

#### مرحله ۴: مدیریت سرویس

```bash
backflip
```

از منوی تعاملی برای موارد زیر استفاده کنید:
- 📊 مشاهده لاگ‌ها و وضعیت
- 🔄 راه‌اندازی مجدد تانل
- ⚙️ ویرایش پیکربندی
- 🔄 به‌روزرسانی سرویس
- 🗑️ حذف Backflip

## ⚙️ فایل پیکربندی

نصبگر فایل `/etc/backflip/config.yaml` را ایجاد می‌کند. مثال:

```yaml
mode: "direct"
server_iran: "iran.example.com"
server_foreign: "us.example.com"
tunnel_port: 443
proxies:
  - local_port: 8080
    remote_host: us.example.com
    remote_port: 8080
  - local_port: 8443
    remote_host: us.example.com
    remote_port: 8443
mux: true
```

### 📋 توضیح پارامترها

| پارامتر | توضیح |
|---------|-------|
| **mode** | `direct` پورت‌های محلی را به هاست‌های دور از طریق `-L` ارسال می‌کند. `reverse` سرویس‌های محلی را از راه دور در دسترس قرار می‌دهد. |
| **server_iran / server_foreign** | نقاط پایانی SSH (مثل `user@host`). سرویس در حالت مستقیم به هاست خارجی و در حالت معکوس به هاست ایرانی متصل می‌شود. |
| **tunnel_port** | پورت SSH مورد استفاده برای تانل اصلی. |
| **proxies** | لیست نگاشت پورت‌ها. به صورت پیش‌فرض `remote_host` همان سرور خارجی وارد شده در نصب است؛ در صورت نیاز مقصد دیگری را دستی وارد کنید. |
| **mux** | SSH ControlMaster را فعال می‌کند تا یک اتصال TCP واحد در تمام نگاشت‌ها استفاده شود. |

> 💡 **نکته**: فایل را به صورت دستی یا از طریق `backflip` → **Edit Settings** به‌روزرسانی کنید. پس از تغییرات، سرویس را مجدداً راه‌اندازی کنید.

## 🔧 آناتومی سرویس

| کامپوننت | مسیر | توضیح |
|-----------|------|-------|
| **فایل سرویس** | `/etc/systemd/system/backflip.service` | فایل سرویس systemd |
| **اجرای اصلی** | `python -m backflip.tunnel /etc/backflip/config.yaml` | دستور اجرای سرویس |
| **لاگ‌ها** | `/var/log/backflip/backflip.log` + `journalctl -u backflip` | فایل‌های لاگ |
| **مسیر کنترل** | `/run/backflip/mux-%r@%h-%p` | مسیر کنترل SSH multiplexing |

### 🔐 فعال‌سازی دوباره MUX با کلید SSH

اگر هنگام نصب رمز عبور وارد کنید، Backflip برای جلوگیری از خطاهای ControlMaster مقدار `mux` را روی `false` می‌گذارد. برای فعال‌سازی مجدد MUX با احراز هویت کلیدی:

1. **روی سرور ایران (کاربر root) کلید بسازید**
   ```bash
   sudo ssh-keygen -t ed25519 -f /root/.ssh/backflip -N ''
   ```

2. **کلید عمومی را روی سرور خارجی نصب کنید**
   ```bash
   sudo ssh-copy-id -i /root/.ssh/backflip root@آدرس-سرور-خارجی
   ```

3. **در فایل `/root/.ssh/config` ارجاع دهید**
   ```ssh-config
   Host backflip-foreign
       HostName آدرس-سرور-خارجی
       User root
       IdentityFile /root/.ssh/backflip
   ```

4. **فایل `/etc/backflip/config.yaml` را ویرایش کنید**
   - مقدار `server_foreign` را `backflip-foreign` قرار دهید
   - فیلد `password` را حذف کنید یا روی `null` بگذارید
   - مقدار `mux` را `true` کنید

5. **سرویس را ریستارت کنید**
   ```bash
   sudo systemctl restart backflip
   ```

از این پس تونل بدون ذخیره رمز و با استفاده از یک اتصال مشترک ControlMaster برقرار می‌شود.

## 🛠️ توسعه

### پیش‌نیازها
- Python 3.10+
- Git

### راه‌اندازی محیط توسعه محلی

```bash
# کلون کردن مخزن
git clone https://github.com/zZedix/BackFlip.git
cd BackFlip

# ایجاد محیط مجازی
python3 -m venv venv
source venv/bin/activate  # در ویندوز: venv\Scripts\activate

# نصب در حالت توسعه
pip install -e .

# اجرای مستقیم تانل
python -m backflip.tunnel path/to/config.yaml
```

### ابزارهای توسعه
- **Linting**: `ruff` یا `flake8`
- **تست**: `pytest` (در صورت اضافه کردن تست‌ها)
- **بررسی نوع**: `mypy`

## 🗑️ حذف نصب

### روش ۱: استفاده از CLI (پیشنهادی)
```bash
backflip
# سپس گزینه "Uninstall" را انتخاب کنید
```

### روش ۲: حذف دستی
```bash
# متوقف و غیرفعال کردن سرویس
sudo systemctl disable --now backflip

# حذف فایل سرویس
sudo rm /etc/systemd/system/backflip.service

# حذف پیکربندی و لاگ‌ها
sudo rm -rf /etc/backflip /var/log/backflip

# حذف پکیج Python
sudo pip3 uninstall backflip

# بارگذاری مجدد systemd
sudo systemctl daemon-reload
```

## 🏗️ معماری پروژه

```
backflip/
├── __init__.py           # مقداردهی اولیه پکیج
├── cli.py                # رابط خط فرمان
├── config.py             # مدیریت پیکربندی
└── tunnel.py             # پیاده‌سازی تانل SSH
scripts/
├── __init__.py
└── install.py            # جادوگر نصب
install.sh                # اسکریپت نصب یک‌خطی
pyproject.toml            # پیکربندی پروژه
README.md / README-fa.md  # مستندات
LICENSE                   # مجوز MIT
```

## 🤝 مشارکت

ما از مشارکت در پروژه Backflip Tunnel استقبال می‌کنیم! در اینجا نحوه کمک شما آورده شده:

1. **فورک کردن مخزن**
2. **ایجاد شاخه جدید**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **ایجاد تغییرات**
   - از سبک کد موجود پیروی کنید
   - برای منطق پیچیده کامنت اضافه کنید
   - در صورت نیاز مستندات را به‌روزرسانی کنید
4. **اضافه کردن تست برای عملکرد جدید**
   ```bash
   pytest tests/
   ```
5. **اطمینان از عبور تمام تست‌ها**
6. **ارسال pull request**

### راه‌اندازی محیط توسعه

```bash
# کلون کردن مخزن
git clone https://github.com/zZedix/BackFlip.git
cd BackFlip

# نصب در حالت توسعه
pip install -e .

# اجرای تست‌ها
pytest tests/
```

## 💰 حمایت مالی

اگر Backflip Tunnel برای شما مفید است و می‌خواهید از توسعه آن حمایت کنید، می‌توانید کمک مالی کنید:

### کمک‌های مالی ارز دیجیتال

- **Bitcoin (BTC)**: `bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh`
- **Ethereum (ETH)**: `0x8Fb2c4AF74e072CefC14A4E9927a1F86F1cd492c`
- **Tron (TRX)**: `TD43B2eT7JC8upacMarcmBBGFkjy75QJHK`
- **USDT (BEP20)**: `0x8Fb2c4AF74e072CefC14A4E9927a1F86F1cd492c`
- **TON**: `UQAFTGSc2YRNGQwwuTyD0Q-eB7pB0BNG0yvx5jVYAJWFu-y6`

### راه‌های دیگر حمایت

- ⭐ **ستاره دادن به مخزن** اگر مفید است
- 🐛 **گزارش باگ** و پیشنهاد بهبود
- 📖 **بهبود مستندات** و ترجمه‌ها
- 🔗 **اشتراک‌گذاری با دیگران** که ممکن است مفید باشد

## 📄 مجوز

این پروژه تحت **مجوز MIT** منتشر شده است - برای جزئیات به فایل [LICENSE](LICENSE) مراجعه کنید.

```
MIT License

Copyright (c) 2024 Backflip Tunnel

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## ⚠️ سلب مسئولیت

**اطلاعیه مهم قانونی:**

- **هدف آموزشی**: این نرم‌افزار صرفاً برای اهداف آموزشی و تحقیقاتی ارائه شده است.
- **رعایت قوانین**: کاربران مسئول اطمینان از رعایت تمام قوانین و مقررات قابل اجرا در حوزه قضایی خود هستند.
- **عدم ضمانت**: نرم‌افزار "همان‌طور که هست" ارائه شده و هیچ ضمانت یا تضمین عملکردی ندارد.
- **اطلاعیه امنیتی**: در حالی که ما تلاش می‌کنیم امنیت را حفظ کنیم، کاربران باید اقدامات امنیتی اضافی مناسب برای مورد استفاده خود پیاده‌سازی کنند.
- **استفاده از شبکه**: کاربران مسئول اطمینان از رعایت شرایط خدمات ISP و مقررات محلی در استفاده از شبکه هستند.
- **عدم مسئولیت**: توسعه‌دهندگان و مشارکت‌کنندگان مسئول سوءاستفاده، خسارت یا مسائل قانونی ناشی از استفاده از این نرم‌افزار نیستند.

**با استفاده از این نرم‌افزار، شما تأیید می‌کنید که این سلب مسئولیت را خوانده و درک کرده‌اید و موافقت می‌کنید که نرم‌افزار را با مسئولیت خود استفاده کنید.**

---

<div align="center">

**Backflip تحت مجوز MIT منتشر شده است** 📄

[![Made with ❤️](https://img.shields.io/badge/Made%20with-❤️-red?style=flat-square)](https://github.com/zZedix/BackFlip)

</div>