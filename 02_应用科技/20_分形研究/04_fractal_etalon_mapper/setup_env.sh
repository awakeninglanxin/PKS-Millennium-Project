#!/bin/bash
# ============================================================
# AutoDL + 阿里云 OSS 环境变量配置
# 使用方法：source setup_env.sh
# ============================================================

# 【必改区域】把下面的值替换成你自己的真实信息

# ---------- 阿里云 OSS（云端备份，强烈推荐）----------
export OSS_BUCKET="你的bucket名称"
export OSS_ENDPOINT="https://oss-cn-hangzhou.aliyuncs.com"
export OSS_ACCESS_KEY_ID="你的AccessKey ID"
export OSS_ACCESS_KEY_SECRET="你的AccessKey Secret"

# ---------- AutoDL 关机 API（可选，不配则走系统关机）----------
export AUTODL_API_TOKEN="你的AutoDL API Token"
export AUTODL_INSTANCE_ID="你的实例ID"

# ============================================================
# 配置检查
# ============================================================
echo "📋 环境变量配置检查"
echo "========================================"
[ -n "$OSS_BUCKET" ] && echo "✅ OSS_BUCKET      $OSS_BUCKET" || echo "⚠️  OSS_BUCKET      未配置"
[ -n "$OSS_ENDPOINT" ] && echo "✅ OSS_ENDPOINT    $OSS_ENDPOINT" || echo "⚠️  OSS_ENDPOINT    未配置"
[ -n "$OSS_ACCESS_KEY_ID" ] && echo "✅ OSS_ACCESS_KEY  ***" || echo "⚠️  OSS_ACCESS_KEY  未配置"
[ -n "$AUTODL_API_TOKEN" ] && echo "✅ AUTODL_TOKEN    ***" || echo "ℹ️  AUTODL_TOKEN    未配置(将用系统关机)"
echo "========================================"
