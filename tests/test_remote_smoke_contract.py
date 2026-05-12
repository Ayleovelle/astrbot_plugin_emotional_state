import unittest
import ast
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NODE_FALLBACK_SNIPPET = [
    '$node = "$HOME\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\node\\bin\\node.exe"',
    '$nodeModules = "$HOME\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\node\\node_modules"',
    'if (Test-Path $node) { $env:NODE_PATH = $nodeModules } else { $node = "node" }',
]


class RemoteSmokeContractTests(unittest.TestCase):
    def _metadata_value(self, name):
        for line in (ROOT / "metadata.yaml").read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{name}:"):
                return line.split(":", 1)[1].strip().strip('"')
        self.fail(f"metadata.yaml missing {name}")

    def _powershell_env_values(self, text, name):
        return re.findall(rf'\$env:{re.escape(name)}\s*=\s*"([^"]+)"', text)

    def _node_fallback_lines(self, text):
        return [
            line
            for line in text.splitlines()
            if (
                line.startswith("$node = ")
                or line.startswith("$nodeModules = ")
                or line.startswith("if (Test-Path $node)")
            )
        ]

    def test_readme_documents_remote_smoke_without_real_credentials(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("scripts\\remote_smoke_playwright.js", readme)
        self.assertIn("scripts\\plugin_zip_preflight.js", readme)
        self.assertIn("codex-primary-runtime", readme)
        self.assertIn("$env:NODE_PATH", readme)
        self.assertIn("& $node scripts\\remote_smoke_playwright.js", readme)
        self.assertIn("& $node scripts\\plugin_zip_preflight.js", readme)
        self.assertIn("ASTRBOT_REMOTE_URL", readme)
        self.assertIn("ASTRBOT_REMOTE_USERNAME", readme)
        self.assertIn("ASTRBOT_REMOTE_PASSWORD", readme)
        self.assertIn("ASTRBOT_EXPECT_PLUGIN", readme)
        self.assertIn("ASTRBOT_EXPECT_PLUGIN_VERSION", readme)
        self.assertIn("ASTRBOT_EXPECT_PLUGIN_DISPLAY_NAME", readme)
        self.assertIn("expectedPluginChecks.ok", readme)
        self.assertIn("expectedPluginChecks.ok=true", readme)
        self.assertIn("expectedPluginRuntime", readme)
        self.assertIn("expectedFailedPlugin", readme)
        self.assertIn("failedPluginSummary", readme)
        self.assertIn("hasExpectedPluginFailure", readme)
        self.assertIn("unrelatedCount", readme)
        self.assertIn("apiHealth", readme)
        self.assertIn("uiProbeStatus", readme)
        self.assertIn("selectorCounts", readme)
        self.assertIn("尽力诊断", readme)
        self.assertIn("/api/plugin/source/get-failed-plugins", readme)
        self.assertIn("退出码 `9`", readme)
        self.assertIn("退出码 `5`", readme)
        self.assertIn("其他插件的失败记录", readme)
        self.assertIn("containsExpectedPlugin=true", readme)
        self.assertIn("expectedPluginRuntime.activated !== false", readme)
        self.assertIn("远程安装插件后", readme)
        self.assertIn("作为 AstrBot 插件安装，作为情绪状态层运行", readme)
        self.assertIn("scripts\\package_plugin.py", readme)
        self.assertIn("raw/", readme)
        self.assertIn("task_plan.md", readme)
        self.assertIn("findings.md", readme)
        self.assertIn("progress.md", readme)
        self.assertIn("API 健康摘要", readme)
        self.assertIn("UI 尽力诊断字段", readme)
        self.assertIn("内置 Node 文档契约", readme)
        remote_host_sentinel = "154.36." + "178.25"
        remote_password_sentinel = "1234" + "1234"
        self.assertNotIn(remote_host_sentinel, readme)
        self.assertNotIn(remote_password_sentinel, readme)
        self.assertNotIn("\nnode --check scripts\\remote_smoke_playwright.js", readme)
        self.assertNotIn("\nnode scripts\\remote_smoke_playwright.js", readme)

    def test_readme_test_matrix_documents_current_contract_scope(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        section = readme.split("### 当前测试覆盖方向", 1)[1].split(
            "### 持久迭代计划",
            1,
        )[0]
        expected_fragments = (
            "命令/alias",
            "LLM 工具注册名",
            "assessment_timing",
            "类型化配置表",
            "Protocol 方法面",
            "required tuple",
            "schema-version",
            "metadata 驱动的插件身份",
            "zip/env 示例",
            "slug/badge/version/display_name",
        )

        for fragment in expected_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, section)

    def test_release_checklist_uses_bundled_node_fallback(self):
        checklist = (ROOT / "docs" / "release_branch_sync_checklist.md").read_text(
            encoding="utf-8",
        )

        self.assertIn("codex-primary-runtime", checklist)
        self.assertIn("$env:NODE_PATH", checklist)
        self.assertIn("& $node --check scripts\\remote_smoke_playwright.js", checklist)
        self.assertIn(
            "& $node --check scripts\\remote_cleanup_plugin_playwright.js",
            checklist,
        )
        self.assertIn(
            "& $node --check scripts\\remote_install_upload_playwright.js",
            checklist,
        )
        self.assertIn(
            "& $node --check scripts\\remote_emotion_benchmark_playwright.js",
            checklist,
        )
        self.assertIn(
            "& $node --check scripts\\run_remote_emotion_benchmark_batches.js",
            checklist,
        )
        self.assertIn("& $node --check scripts\\plugin_zip_preflight.js", checklist)
        self.assertIn("& $node scripts\\remote_smoke_playwright.js", checklist)
        self.assertNotIn("\nnode --check scripts\\remote_smoke_playwright.js", checklist)
        self.assertNotIn("\nnode scripts\\remote_smoke_playwright.js", checklist)

    def test_node_fallback_is_consistent_and_before_commands(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        checklist = (ROOT / "docs" / "release_branch_sync_checklist.md").read_text(
            encoding="utf-8",
        )
        fallback = self._node_fallback_lines(readme)

        self.assertEqual(NODE_FALLBACK_SNIPPET, fallback)
        self.assertEqual(fallback, self._node_fallback_lines(checklist))
        self.assertLess(readme.index("codex-primary-runtime"), readme.index("& $node scripts\\remote_smoke_playwright.js"))
        self.assertLess(checklist.index("codex-primary-runtime"), checklist.index("& $node --check scripts\\remote_smoke_playwright.js"))

    def test_remote_smoke_expected_runtime_values_match_metadata(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        checklist = (ROOT / "docs" / "release_branch_sync_checklist.md").read_text(
            encoding="utf-8",
        )
        expected_version = self._metadata_value("version")
        expected_display_name = self._metadata_value("display_name")

        for document_name, document in (
            ("README.md", readme),
            ("docs/release_branch_sync_checklist.md", checklist),
        ):
            with self.subTest(document=document_name):
                self.assertEqual(
                    [expected_version],
                    self._powershell_env_values(
                        document,
                        "ASTRBOT_EXPECT_PLUGIN_VERSION",
                    ),
                )
                self.assertEqual(
                    [expected_display_name],
                    self._powershell_env_values(
                        document,
                        "ASTRBOT_EXPECT_PLUGIN_DISPLAY_NAME",
                    ),
                )

    def test_documented_plugin_identity_values_match_metadata(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        checklist = (ROOT / "docs" / "release_branch_sync_checklist.md").read_text(
            encoding="utf-8",
        )
        plugin_name = self._metadata_value("name")
        plugin_license = self._metadata_value("license")
        expected_zip = f"dist\\{plugin_name}.zip"

        for document_name, document in (
            ("README.md", readme),
            ("docs/release_branch_sync_checklist.md", checklist),
        ):
            with self.subTest(document=document_name):
                expected_plugin_values = self._powershell_env_values(
                    document,
                    "ASTRBOT_EXPECT_PLUGIN",
                )
                self.assertGreaterEqual(len(expected_plugin_values), 1)
                self.assertEqual(
                    {plugin_name},
                    set(expected_plugin_values),
                )
                if "ASTRBOT_REMOTE_INSTALL_ZIP" in document:
                    self.assertEqual(
                        [expected_zip],
                        self._powershell_env_values(
                            document,
                            "ASTRBOT_REMOTE_INSTALL_ZIP",
                        ),
                    )
                self.assertIn(
                    f"& $node scripts\\plugin_zip_preflight.js {expected_zip} {plugin_name}",
                    document,
                )
                self.assertIn(plugin_license, document)
                self.assertIn(
                    f"py -3.13 scripts\\package_plugin.py --output {expected_zip}",
                    document,
                )

        for runtime_file in (
            "__init__.py",
            "agent_identity.py",
            "main.py",
            "emotion_engine.py",
            "group_atmosphere_engine.py",
            "humanlike_engine.py",
            "lifelike_learning_engine.py",
            "personality_drift_engine.py",
            "integrated_self.py",
            "moral_repair_engine.py",
            "fallibility_engine.py",
            "psychological_screening.py",
            "prompts.py",
            "public_api.py",
            "LICENSE",
            "requirements.txt",
        ):
            with self.subTest(runtime_file=runtime_file):
                self.assertIn(runtime_file, readme)
                self.assertIn(runtime_file, checklist)

    def test_documented_plugin_slug_references_match_metadata(self):
        plugin_name = self._metadata_value("name")
        repo_url = self._metadata_value("repo")
        repo_slugs = set(re.findall(r"astrbot_plugin_[A-Za-z0-9_]+", repo_url))
        allowed_external_references = {"astrbot_plugin_volcengine_asr"} | repo_slugs

        for relative_path in (
            Path("README.md"),
            Path("docs") / "release_branch_sync_checklist.md",
        ):
            document = (ROOT / relative_path).read_text(encoding="utf-8")
            slugs = set(re.findall(r"astrbot_plugin_[A-Za-z0-9_]+", document))

            with self.subTest(document=str(relative_path)):
                self.assertGreaterEqual(slugs, {plugin_name})
                self.assertEqual(
                    set(),
                    slugs - {plugin_name} - allowed_external_references,
                )

    def test_readme_badges_and_compatibility_match_metadata(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        version = self._metadata_value("version")
        astrbot_version = self._metadata_value("astrbot_version")
        encoded_astrbot = (
            astrbot_version
            .replace(">", "%3E")
            .replace("=", "%3D")
            .replace("<", "%3C")
            .replace(",", "%2C")
        )

        self.assertIn(f"![版本 {version}]", readme)
        self.assertIn(f"https://img.shields.io/badge/version-{version}-blue", readme)
        self.assertIn(f"![AstrBot {astrbot_version}]", readme)
        self.assertIn(
            f"https://img.shields.io/badge/AstrBot-{encoded_astrbot}-green",
            readme,
        )
        self.assertIn(f'astrbot_version: "{astrbot_version}"', readme)

    def test_readme_is_concise_release_page_not_iteration_archive(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("AstrBot 多维情绪状态插件", readme)
        self.assertIn("通过 Star 插件载体部署", readme)
        self.assertIn("作为 AstrBot 插件安装，作为情绪状态层运行", readme)
        self.assertIn("https://github.com/Ayleovelle/astrbot_plugin_qq_voice_call", readme)
        self.assertIn("docs/theory.md", readme)
        self.assertNotIn("0.0.2-beta-pr-1", readme)
        self.assertNotIn("展开逐轮工程迭代明细", readme)
        self.assertNotIn("顶刊证据映射", readme)

    def test_experimental_release_docs_keep_version_and_branch_scope(self):
        version = self._metadata_value("version")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        remote_testing = (ROOT / "docs" / "remote_testing.md").read_text(
            encoding="utf-8",
        )
        branching = (ROOT / "docs" / "branching_strategy.md").read_text(
            encoding="utf-8",
        )
        checklist = (
            ROOT / "docs" / "release_branch_sync_checklist.md"
        ).read_text(encoding="utf-8")

        self.assertEqual(version, "0.1.0-exp.1")
        self.assertIn("experiment/state-layer-0.1.0-exp.1", branching)
        self.assertIn("experiment/state-layer-0.1.0-exp.1", checklist)
        self.assertIn("历史基线实测结论", remote_testing)
        self.assertIn("不是独立安装形态", branching)
        self.assertIn("$env:ASTRBOT_EXPECT_PLUGIN_VERSION = \"0.1.0-exp.1\"", remote_testing)
        self.assertIn("$env:ASTRBOT_EXPECT_PLUGIN_DISPLAY_NAME = \"多维情绪状态\"", remote_testing)
        self.assertIn("当前实验发布目标版本是 `0.1.0-exp.1`", remote_testing)
        self.assertNotIn("先在 `main` 上完成当前迭代验证", branching)
        self.assertNotIn("After `main` is clean:", checklist)
        self.assertNotIn("不是独立" + "产品", branching)
        self.assertNotIn("AstrBot Emotional " + "Agent", readme)
        self.assertNotIn("作为 Star 安装，作为 " + "Agent 运行", readme)

    def test_remote_smoke_script_uses_environment_credentials(self):
        script = (ROOT / "scripts" / "remote_smoke_playwright.js").read_text(
            encoding="utf-8",
        )

        self.assertIn("ASTRBOT_REMOTE_USERNAME", script)
        self.assertIn("ASTRBOT_REMOTE_PASSWORD", script)
        self.assertIn("ASTRBOT_REMOTE_URL", script)
        self.assertIn("ASTRBOT_REMOTE_ARTIFACT_DIR", script)
        self.assertIn("apiHealth", script)
        self.assertIn("statVersion", script)
        self.assertIn("pluginGet", script)
        self.assertIn("expectedFailedPlugin", script)
        self.assertIn("expectedPluginChecks", script)
        self.assertIn("expectedPluginDrift", script)
        self.assertIn("hasDrift", script)
        self.assertIn("does not overwrite an existing formal plugin directory", script)
        self.assertIn("versionMatches", script)
        self.assertIn("displayNameMatches", script)
        self.assertIn("failedPluginSummary", script)
        self.assertIn("summarizeFailedPlugins", script)
        self.assertIn("hasExpectedPluginFailure", script)
        self.assertIn("unrelatedCount", script)
        self.assertIn("expectedPluginRuntime", script)
        self.assertIn("hasExpectedPlugin: hasExpectedPluginInUi", script)
        self.assertIn("hasExpectedPluginDisplayName", script)
        self.assertIn("hasExpectedPluginInUi", script)
        self.assertIn("titleHasExpectedPlugin", script)
        self.assertIn("waitForExtensionUi", script)
        self.assertIn("uiProbeStatus", script)
        self.assertIn("best_effort_timeout", script)
        self.assertIn("selectorCounts", script)
        self.assertIn("bodyTextPreview", script)
        self.assertIn("ASTRBOT_EXPECT_PLUGIN_VERSION", script)
        self.assertIn("ASTRBOT_EXPECT_PLUGIN_DISPLAY_NAME", script)
        self.assertIn("process.exitCode = 5", script)
        self.assertIn("process.exitCode = 6", script)
        self.assertIn("process.exitCode = 7", script)
        self.assertIn("process.exitCode = 8", script)
        self.assertIn("process.exitCode = 9", script)
        self.assertIn("failedPlugins.status !== 200", script)
        self.assertIn("activated === false", script)
        remote_password_sentinel = "1234" + "1234"
        remote_host_sentinel = "154.36." + "178.25"
        self.assertNotIn(remote_password_sentinel, script)
        self.assertNotIn(remote_host_sentinel, script)
        self.assertNotIn("username = \"root\"", script)
        self.assertNotIn("password = \"", script)

    def test_remote_install_script_requires_explicit_confirmation(self):
        script = (
            ROOT / "scripts" / "remote_install_upload_playwright.js"
        ).read_text(encoding="utf-8")
        preflight = (
            ROOT / "scripts" / "plugin_zip_preflight.js"
        ).read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        checklist = (ROOT / "docs" / "release_branch_sync_checklist.md").read_text(
            encoding="utf-8",
        )

        self.assertIn("ASTRBOT_REMOTE_INSTALL_CONFIRM", script)
        self.assertIn("ASTRBOT_REMOTE_INSTALL_ZIP", script)
        self.assertIn("ASTRBOT_EXPECT_PLUGIN", script)
        self.assertIn("/api/plugin/install-upload", script)
        self.assertIn("assertZipLooksUploadable", script)
        self.assertIn('toString("base64")', script)
        self.assertIn("atob(base64)", script)
        self.assertIn('credentials: "include"', script)
        self.assertNotIn("Array.from(zipBytes)", script)
        self.assertNotIn("page.context().request.post", script)
        self.assertIn("readUInt32LE(0)", preflight)
        self.assertIn("readUInt16LE(26)", preflight)
        self.assertIn("readCentralDirectoryNames", preflight)
        self.assertIn("readZipEntryText", preflight)
        self.assertIn("readMetadataName", preflight)
        self.assertIn("0x02014b50", preflight)
        for required_entry in (
            "__init__.py",
            "metadata.yaml",
            "main.py",
            "emotion_engine.py",
            "humanlike_engine.py",
            "lifelike_learning_engine.py",
            "personality_drift_engine.py",
            "integrated_self.py",
            "moral_repair_engine.py",
            "fallibility_engine.py",
            "psychological_screening.py",
            "prompts.py",
            "public_api.py",
            "README.md",
            "LICENSE",
            "requirements.txt",
            "_conf_schema.json",
        ):
            with self.subTest(required_entry=required_entry):
                self.assertIn(required_entry, preflight)
                self.assertIn(required_entry, readme)
        self.assertIn("\"tests\"", preflight)
        self.assertIn("\"scripts\"", preflight)
        self.assertIn("\"output\"", preflight)
        self.assertIn("\"raw\"", preflight)
        self.assertIn("Zip entry must be under", preflight)
        self.assertIn("Zip entry must not contain parent traversal", preflight)
        self.assertIn("metadata.yaml name must be", preflight)
        self.assertIn("alreadyInstalled", script)
        self.assertIn("目录 ${expectedPlugin} 已存在", script)
        self.assertIn("already_installed_no_overwrite", script)
        self.assertIn("overwriteAttempted: false", script)
        self.assertIn("formalPluginDirectoryPreserved", script)
        self.assertIn("cleanupAlreadyInstalledFailure", script)
        self.assertIn("/api/plugin/uninstall-failed", script)
        self.assertIn("plugin_upload_${expectedPlugin}", script)
        self.assertIn("delete_config: false", script)
        self.assertIn("delete_data: false", script)
        for document in (readme, checklist):
            with self.subTest(document_contains_failed_upload_cleanup=True):
                self.assertIn("uninstall-failed", document)
                self.assertIn("delete_config=false", document)
                self.assertIn("delete_data=false", document)
                self.assertIn("already_installed_no_overwrite", document)
                self.assertIn("overwriteAttempted=false", document)
        self.assertIn("ASTRBOT_REMOTE_USERNAME", script)
        self.assertIn("ASTRBOT_REMOTE_PASSWORD", script)
        remote_password_sentinel = "1234" + "1234"
        remote_host_sentinel = "154.36." + "178.25"
        self.assertNotIn(remote_password_sentinel, script)
        self.assertNotIn(remote_host_sentinel, script)
        self.assertNotIn("username = \"root\"", script)
        self.assertNotIn("password = \"", script)

    def test_remote_cleanup_script_is_exactly_allowlisted(self):
        script = (
            ROOT / "scripts" / "remote_cleanup_plugin_playwright.js"
        ).read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        checklist = (ROOT / "docs" / "release_branch_sync_checklist.md").read_text(
            encoding="utf-8",
        )

        self.assertIn('ALLOWED_PLUGIN = "astrbot_plugin_qq_voice_call"', script)
        self.assertIn("ASTRBOT_REMOTE_CLEAN_CONFIRM", script)
        self.assertIn("ASTRBOT_REMOTE_CLEAN_FORMAL", script)
        self.assertIn("ASTRBOT_REMOTE_CLEAN_FAILED_UPLOAD", script)
        self.assertIn("/api/plugin/uninstall", script)
        self.assertIn("/api/plugin/uninstall-failed", script)
        self.assertIn("plugin_upload_${expectedPlugin}", script)
        self.assertIn("pluginMatchesExactly", script)
        self.assertIn("delete_config: false", script)
        self.assertIn("delete_data: false", script)
        self.assertIn("astrbot_plugin_livingmemory", script)
        self.assertIn("untouchedByDesign: true", script)
        self.assertNotIn("includes(expectedPlugin)", script)
        self.assertNotIn("startsWith(expectedPlugin)", script)
        self.assertNotIn("method: \"DELETE\"", script)
        self.assertNotIn("delete_config: true", script)
        self.assertNotIn("delete_data: true", script)
        for document in (readme, checklist):
            with self.subTest(document_contains_cleanup_contract=True):
                self.assertIn("scripts\\remote_cleanup_plugin_playwright.js", document)
                self.assertIn(
                    '$env:ASTRBOT_REMOTE_CLEAN_CONFIRM = "astrbot_plugin_qq_voice_call"',
                    document,
                )
                self.assertIn(
                    '$env:ASTRBOT_REMOTE_CLEAN_FORMAL = "1"',
                    document,
                )
                self.assertIn(
                    '$env:ASTRBOT_REMOTE_CLEAN_FAILED_UPLOAD = "1"',
                    document,
                )
                self.assertIn("plugin_upload_astrbot_plugin_qq_voice_call", document)
                self.assertIn("delete_config=false", document)
                self.assertIn("delete_data=false", document)
                self.assertIn("LivingMemory", document)

    def test_remote_install_script_only_allows_upload_install_mutation(self):
        script = (
            ROOT / "scripts" / "remote_install_upload_playwright.js"
        ).read_text(encoding="utf-8")
        lowered = script.lower()
        forbidden_fragments = (
            "/api/plugin/delete",
            "/api/plugin/reload",
            "/api/plugin/update",
            "/api/plugin/update-all",
            "/api/config/update",
            "/api/config/save",
            "/api/system/restart",
            "restartastrbot",
            "method: \"delete\"",
            "method:'delete'",
        )

        self.assertIn("/api/plugin/install-upload", lowered)
        self.assertIn("/api/plugin/uninstall-failed", lowered)
        self.assertIn("method: \"post\"", lowered)
        self.assertIn("overwriteattempted: false", lowered)
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, lowered)

    def test_remote_install_script_does_not_persist_credentials_or_sessions(self):
        script = (
            ROOT / "scripts" / "remote_install_upload_playwright.js"
        ).read_text(encoding="utf-8")
        lowered = script.lower()

        self.assertNotIn("dotenv", lowered)
        self.assertNotIn("readfile", lowered.replace("readfilesync(zippath)", ""))
        self.assertNotIn("storagestate", lowered)
        self.assertNotIn("cookie", lowered)
        self.assertNotIn("localstorage", lowered)
        self.assertNotIn("sessionstorage", lowered)

    def test_remote_lifecycle_benchmark_uses_simulated_state_time(self):
        script = (
            ROOT / "scripts" / "remote_emotion_benchmark_playwright.js"
        ).read_text(encoding="utf-8")
        remote_testing = (ROOT / "docs" / "remote_testing.md").read_text(
            encoding="utf-8",
        )

        self.assertIn("benchmark_enable_simulated_time: false", script)
        self.assertIn("benchmark_enable_simulated_time: true", script)
        self.assertIn("benchmark_time_offset_seconds: 0", script)
        self.assertIn("benchmark_time_offset_seconds", script)
        self.assertIn("Math.max(0, Number(durationSeconds) || 0)", script)
        self.assertIn("lifecycle_duration_seconds", script)
        self.assertIn("ASTRBOT_BENCHMARK_RESTORE_CONFIG_AT_END", script)
        self.assertIn("ASTRBOT_BENCHMARK_RESTORE_CONFIG_EACH_SAMPLE", script)
        self.assertIn("final_restore: finalRestore", script)
        self.assertIn("restore_jsonl", script)
        self.assertIn("summarizeRestoreResult", script)
        self.assertIn("plugin_runtime_probe", script)
        self.assertIn("ASTRBOT_EXPECT_PLUGIN_VERSION", script)
        self.assertIn("ASTRBOT_EXPECT_PLUGIN_DISPLAY_NAME", script)
        self.assertIn("redactRemoteTarget(remoteUrl)", script)
        self.assertNotIn("remote_url: remoteUrl", script)
        self.assertIn("ASTRBOT_BENCHMARK_RESTORE_CONFIG_AT_END", remote_testing)
        self.assertIn("ASTRBOT_BENCHMARK_RESTORE_CONFIG_EACH_SAMPLE", remote_testing)
        self.assertIn("plugin_runtime_probe", remote_testing)
        self.assertIn("final_restore.ok", remote_testing)
        self.assertIn("restore.jsonl", remote_testing)
        self.assertIn("remote_target.host_hash", remote_testing)
        self.assertIn("scripts\\remote_state_layer_ab_config.json", remote_testing)
        self.assertIn("legacy_sync_full_injection", remote_testing)
        self.assertIn("experimental_state_layer_diff", remote_testing)

    def test_remote_state_layer_ab_config_documents_experiment_matrix(self):
        config_text = (
            ROOT / "scripts" / "remote_state_layer_ab_config.json"
        ).read_text(encoding="utf-8")
        config = json.loads(config_text)
        schema = json.loads((ROOT / "_conf_schema.json").read_text(encoding="utf-8"))
        schema_keys = set(schema)
        for item in config["matrix"]:
            extra_keys = set(item["config"]) - schema_keys
            self.assertEqual(set(), extra_keys, item["id"])

        self.assertIn("legacy_sync_full_injection", config_text)
        self.assertIn("experimental_state_layer_diff", config_text)
        self.assertIn('"background_post_assessment": false', config_text)
        self.assertIn('"background_post_assessment": true', config_text)
        self.assertIn('"background_post_max_workers": 5', config_text)
        self.assertIn('"state_injection_compact_mode": "diff"', config_text)
        self.assertIn('"enable_group_atmosphere_state": true', config_text)
        self.assertIn('"group_atmosphere_injection_strength": 0.25', config_text)
        self.assertIn('"group_atmosphere_injection_diff_threshold": 0.08', config_text)
        self.assertIn('"benchmark_enable_simulated_time": false', config_text)
        self.assertIn('"benchmark_time_offset_seconds": 0', config_text)

    def test_remote_smoke_script_is_read_only(self):
        script = (ROOT / "scripts" / "remote_smoke_playwright.js").read_text(
            encoding="utf-8",
        )
        lowered = script.lower()
        forbidden_fragments = (
            "/api/plugin/install",
            "/api/plugin/delete",
            "/api/plugin/reload",
            "/api/plugin/update",
            "/api/config/update",
            "/api/config/save",
            "/api/system/restart",
            "restartastrbot",
            "method: \"post\"",
            "method:'post'",
            "method: \"delete\"",
            "method:'delete'",
        )

        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, lowered)

    def test_remote_smoke_artifacts_are_gitignored(self):
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("output/", gitignore)

    def test_readme_public_api_tables_match_protocol_methods(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        tree = ast.parse((ROOT / "public_api.py").read_text(encoding="utf-8"))
        protocol_methods = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name not in {
                "EmotionServiceProtocol",
                "HumanlikeStateServiceProtocol",
                "MoralRepairStateServiceProtocol",
                "LifelikeLearningServiceProtocol",
                "PersonalityDriftServiceProtocol",
                "FallibilityServiceProtocol",
                "GroupAtmosphereServiceProtocol",
            }:
                continue
            for item in node.body:
                if isinstance(item, ast.AsyncFunctionDef):
                    protocol_methods.add(item.name)

        for method in sorted(protocol_methods):
            with self.subTest(method=method):
                self.assertIn(f"`{method}", readme)

        self.assertIn("get_emotion_service", readme)
        self.assertIn("get_humanlike_service", readme)
        self.assertIn("get_moral_repair_service", readme)
        self.assertIn("get_fallibility_service", readme)
        self.assertIn("get_group_atmosphere_service", readme)
        self.assertIn("校验核心方法是否完整", readme)
        self.assertIn("校验公开版本/schema 是否匹配", readme)

    def test_readme_public_api_examples_document_safe_fallbacks(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        livingmemory_section = readme.split(
            "如果 LivingMemory 的接口只能写普通 dict",
            1,
        )[1].split("如果没有 `AstrMessageEvent`", 1)[0]
        humanlike_section = readme.split("### 拟人状态 API", 1)[1].split(
            "### 表达边界",
            1,
        )[0]
        fallback_section = readme.split(
            "如果不能 import helper",
            1,
        )[1].split("### 情绪 API", 1)[0]

        self.assertIn("if emotion:", livingmemory_section)
        self.assertIn("未安装、未激活或版本不匹配", livingmemory_section)
        self.assertIn("不保证公共 API 完整", fallback_section)
        self.assertIn("不会校验版本/schema", fallback_section)
        self.assertIn("enabled=false", humanlike_section)
        self.assertIn("get_humanlike_values", humanlike_section)
        self.assertIn('snapshot.get("enabled")', humanlike_section)
        self.assertIn('values.get("energy")', humanlike_section)


if __name__ == "__main__":
    unittest.main()
