# 📊 Grafana Configuration Guide

## 🔍 Query

```flux
from(bucket: "stock_kpi")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "kpi_result")
  |> filter(fn: (r) => r._field == "kpi_short" or r._field == "kpi_long" or r._field == "kpi_comprehensive")
  |> filter(fn: (r) => r.stock_code =~ /${stock_code:regex}/)
  |> aggregateWindow(every: ${interval}, fn: mean, createEmpty: false)
```

## 📌 What This Query Does

- `every: 1h`: Groups data into 1-hour buckets  
- `fn: mean`: Calculates the average KPI value per hour

---

## ⚙️ Variable Settings

### `stock_code` Variable

**Query Options:**

```flux
import "influxdata/influxdb/schema"
schema.tagValues(bucket: "stock_kpi", tag: "stock_code")
```

### `interval` Variable

**Options:**

```
10m, 30m, 1h, 6h, 12h, 1d, 7d, 14d, 30d
```

---

## 🔐 InfluxDB API Token Setup

1. Go to **InfluxDB**
2. Click **Load Data** → **API Tokens**
3. Generate a token
4. Pass the token to the **stock generator Docker container** as an environment variable
