"""
Comprehensive tests for the dependency resolution module.

Tests cover:
- Version parsing and comparison
- Requirement parsing
- Version conflict resolution
- Dependency merging
- Error cases and edge cases
"""

import tempfile
from pathlib import Path

import pytest

from dockrion_sdk.dependencies import (
    DependencyConflictError,
    DependencyMerger,
    merge_dependencies,
    parse_requirement,
    parse_requirements_file,
    parse_requirements_string,
    parse_version,
    parse_version_constraint,
    resolve_version_conflict,
)
from dockrion_sdk.dependencies.resolver import (
    ConflictResolution,
    VersionResolver,
)
from dockrion_sdk.dependencies.version import VersionOperator

# ============================================================================
# Version Parsing Tests
# ============================================================================


class TestVersionParsing:
    """Tests for version parsing."""

    def test_parse_simple_version(self):
        """Test parsing simple version like 1.0.0."""
        v = parse_version("1.0.0")
        assert v.major == 1
        assert v.minor == 0
        assert v.patch == 0

    def test_parse_version_without_patch(self):
        """Test parsing version like 1.0."""
        v = parse_version("1.0")
        assert v.major == 1
        assert v.minor == 0
        assert v.patch == 0

    def test_parse_version_major_only(self):
        """Test parsing version like 1."""
        v = parse_version("1")
        assert v.major == 1
        assert v.minor == 0
        assert v.patch == 0

    def test_parse_prerelease_alpha(self):
        """Test parsing alpha version."""
        v = parse_version("1.0.0a1")
        assert v.major == 1
        assert v.minor == 0
        assert v.patch == 0
        assert v.pre_release == "a"
        assert v.pre_release_num == 1

    def test_parse_prerelease_beta(self):
        """Test parsing beta version."""
        v = parse_version("2.5.0beta2")
        assert v.major == 2
        assert v.minor == 5
        assert v.patch == 0
        assert v.pre_release == "beta"
        assert v.pre_release_num == 2

    def test_parse_prerelease_rc(self):
        """Test parsing release candidate."""
        v = parse_version("3.0.0rc1")
        assert v.major == 3
        assert v.minor == 0
        assert v.patch == 0
        assert v.pre_release == "rc"
        assert v.pre_release_num == 1

    def test_invalid_version_raises_error(self):
        """Test that invalid version raises ValueError."""
        with pytest.raises(ValueError):
            parse_version("not.a.version")

        with pytest.raises(ValueError):
            parse_version("1.2.3.4")


class TestVersionComparison:
    """Tests for version comparison."""

    def test_version_equality(self):
        """Test version equality."""
        assert parse_version("1.0.0") == parse_version("1.0.0")
        assert parse_version("1.0") == parse_version("1.0.0")

    def test_version_less_than(self):
        """Test version less than comparison."""
        assert parse_version("1.0.0") < parse_version("2.0.0")
        assert parse_version("1.0.0") < parse_version("1.1.0")
        assert parse_version("1.0.0") < parse_version("1.0.1")
        assert parse_version("1.0.0a1") < parse_version("1.0.0")
        assert parse_version("1.0.0a1") < parse_version("1.0.0b1")

    def test_version_greater_than(self):
        """Test version greater than comparison."""
        assert parse_version("2.0.0") > parse_version("1.0.0")
        assert parse_version("1.1.0") > parse_version("1.0.0")
        assert parse_version("1.0.0") > parse_version("1.0.0rc1")


class TestVersionConstraint:
    """Tests for version constraints."""

    def test_parse_constraint_ge(self):
        """Test parsing >= constraint."""
        c = parse_version_constraint(">=1.0.0")
        assert c.operator == VersionOperator.GE
        assert c.version == parse_version("1.0.0")

    def test_parse_constraint_eq(self):
        """Test parsing == constraint."""
        c = parse_version_constraint("==2.5.0")
        assert c.operator == VersionOperator.EQ
        assert c.version == parse_version("2.5.0")

    def test_parse_constraint_lt(self):
        """Test parsing < constraint."""
        c = parse_version_constraint("<3.0.0")
        assert c.operator == VersionOperator.LT
        assert c.version == parse_version("3.0.0")

    def test_constraint_satisfaction_ge(self):
        """Test >= constraint satisfaction."""
        c = parse_version_constraint(">=1.5.0")
        assert c.is_satisfied_by(parse_version("1.5.0"))
        assert c.is_satisfied_by(parse_version("2.0.0"))
        assert not c.is_satisfied_by(parse_version("1.4.0"))

    def test_constraint_satisfaction_lt(self):
        """Test < constraint satisfaction."""
        c = parse_version_constraint("<2.0.0")
        assert c.is_satisfied_by(parse_version("1.9.9"))
        assert not c.is_satisfied_by(parse_version("2.0.0"))
        assert not c.is_satisfied_by(parse_version("2.0.1"))

    def test_constraint_satisfaction_eq(self):
        """Test == constraint satisfaction."""
        c = parse_version_constraint("==1.2.3")
        assert c.is_satisfied_by(parse_version("1.2.3"))
        assert not c.is_satisfied_by(parse_version("1.2.4"))


# ============================================================================
# Requirement Parsing Tests
# ============================================================================


class TestRequirementParsing:
    """Tests for requirement parsing."""

    def test_parse_simple_requirement(self):
        """Test parsing simple requirement."""
        req = parse_requirement("pydantic>=2.5.0")
        assert req is not None
        assert req.name == "pydantic"
        assert len(req.constraints) == 1
        assert req.constraints[0].operator == VersionOperator.GE

    def test_parse_requirement_with_extras(self):
        """Test parsing requirement with extras."""
        req = parse_requirement("uvicorn[standard]>=0.27.0")
        assert req is not None
        assert req.name == "uvicorn"
        assert "standard" in req.extras

    def test_parse_requirement_multiple_constraints(self):
        """Test parsing requirement with multiple constraints."""
        req = parse_requirement("langchain>=0.1.0,<1.0.0")
        assert req is not None
        assert req.name == "langchain"
        assert len(req.constraints) == 2

    def test_parse_requirement_with_marker(self):
        """Test parsing requirement with environment marker."""
        req = parse_requirement('numpy>=1.20.0; python_version>="3.8"')
        assert req is not None
        assert req.name == "numpy"
        assert req.marker == 'python_version>="3.8"'

    def test_parse_requirement_no_version(self):
        """Test parsing requirement without version."""
        req = parse_requirement("requests")
        assert req is not None
        assert req.name == "requests"
        assert len(req.constraints) == 0

    def test_parse_comment_returns_none(self):
        """Test that comments return None."""
        assert parse_requirement("# This is a comment") is None

    def test_parse_empty_line_returns_none(self):
        """Test that empty lines return None."""
        assert parse_requirement("") is None
        assert parse_requirement("   ") is None

    def test_parse_option_returns_none(self):
        """Test that pip options return None."""
        assert parse_requirement("-r base.txt") is None
        assert parse_requirement("--index-url https://pypi.org") is None


class TestRequirementsString:
    """Tests for parsing requirements from strings."""

    def test_parse_requirements_string(self):
        """Test parsing multi-line requirements."""
        content = """
        # Core dependencies
        pydantic>=2.5.0
        fastapi>=0.109.0

        # Optional
        langchain>=0.3.0
        """
        reqs = parse_requirements_string(content)
        assert len(reqs) == 3
        assert reqs[0].name == "pydantic"
        assert reqs[1].name == "fastapi"
        assert reqs[2].name == "langchain"


class TestRequirementsFile:
    """Tests for parsing requirements from files."""

    def test_parse_requirements_file(self):
        """Test parsing requirements.txt file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("pydantic>=2.5.0\n")
            f.write("fastapi>=0.109.0\n")
            f.write("# comment\n")
            f.write("requests\n")
            f.flush()

            reqs = parse_requirements_file(Path(f.name))
            assert len(reqs) == 3

    def test_parse_missing_file_raises_error(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parse_requirements_file(Path("/nonexistent/requirements.txt"))


# ============================================================================
# Version Conflict Resolution Tests
# ============================================================================


class TestVersionResolver:
    """Tests for version conflict resolution."""

    def test_user_package_not_in_dockrion(self):
        """Test that user-only packages are accepted."""
        resolver = VersionResolver(framework="langgraph")
        req = parse_requirement("langchain-openai>=0.1.0")
        assert req is not None
        result = resolver.resolve(req)
        assert result.resolution == ConflictResolution.USER_OVERRIDE
        assert result.source == "user"

    def test_user_compatible_version_overrides(self):
        """Test that compatible user version overrides dockrion."""
        resolver = VersionResolver()
        # User specifies pydantic>=2.6.0, dockrion needs >=2.5
        req = parse_requirement("pydantic>=2.6.0")
        assert req is not None
        result = resolver.resolve(req)
        assert result.resolution == ConflictResolution.USER_OVERRIDE

    def test_user_incompatible_core_raises_error(self):
        """Test that incompatible core dependency raises error."""
        resolver = VersionResolver()
        # User specifies pydantic==1.0.0, dockrion needs >=2.5
        req = parse_requirement("pydantic==1.0.0")
        assert req is not None
        with pytest.raises(DependencyConflictError) as exc_info:
            resolver.resolve(req)
        assert "pydantic" in str(exc_info.value)
        assert "core" in str(exc_info.value).lower()

    def test_user_no_version_uses_dockrion(self):
        """Test that user package without version uses dockrion's."""
        resolver = VersionResolver()
        req = parse_requirement("pydantic")
        assert req is not None
        result = resolver.resolve(req)
        assert result.resolution == ConflictResolution.DOCKRION_WINS

    def test_optional_package_user_wins(self):
        """Test that optional packages allow user override."""
        resolver = VersionResolver()
        # langfuse is optional - user version should win
        req = parse_requirement("langfuse>=1.0.0")
        assert req is not None
        result = resolver.resolve(req)
        assert result.resolution == ConflictResolution.USER_OVERRIDE


class TestResolveVersionConflict:
    """Tests for the convenience function."""

    def test_resolve_compatible_versions(self):
        """Test resolving compatible versions."""
        result = resolve_version_conflict(
            user_requirement="pydantic>=2.6.0",
            dockrion_constraint=">=2.5",
            package_name="pydantic",
        )
        assert result.resolution == ConflictResolution.USER_OVERRIDE


# ============================================================================
# Dependency Merger Tests
# ============================================================================


class TestDependencyMerger:
    """Tests for the dependency merger."""

    def test_merger_basic(self):
        """Test basic dependency merging."""
        merger = DependencyMerger(framework="langgraph")
        result = merger.merge()

        assert len(result.requirements) > 0
        # Should include core deps
        assert any("pydantic" in r for r in result.requirements)
        assert any("fastapi" in r for r in result.requirements)
        # Should include langgraph deps
        assert any("langgraph" in r for r in result.requirements)

    def test_merger_with_extra_dependencies(self):
        """Test merging with extra dependencies."""
        merger = DependencyMerger(framework="langchain")
        result = merger.merge(extra_dependencies=["langchain-openai>=0.1.0"])

        assert any("langchain-openai" in r for r in result.requirements)

    def test_merger_with_user_requirements_file(self):
        """Test merging with user requirements file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("langchain-anthropic>=0.1.0\n")
            f.write("some-custom-package>=1.0.0\n")
            f.flush()

            merger = DependencyMerger(framework="langgraph")
            result = merger.merge(user_requirements_file=Path(f.name))

            assert any("langchain-anthropic" in r for r in result.requirements)
            assert any("some-custom-package" in r for r in result.requirements)

    def test_merger_user_override_logged(self):
        """Test that user overrides are tracked."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            # User specifies a compatible but different version
            f.write("fastapi>=0.110.0\n")
            f.flush()

            merger = DependencyMerger(framework="custom")
            result = merger.merge(user_requirements_file=Path(f.name))

            # fastapi should be in user_overrides since user specified a version
            assert "fastapi" in result.user_overrides

    def test_merger_observability_langfuse(self):
        """Test that langfuse is included when enabled."""
        merger = DependencyMerger(
            framework="custom",
            observability={"langfuse": True},
        )
        result = merger.merge()

        assert any("langfuse" in r for r in result.requirements)

    def test_merger_observability_langsmith(self):
        """Test that langsmith is included when enabled."""
        merger = DependencyMerger(
            framework="custom",
            observability={"langsmith": True},
        )
        result = merger.merge()

        assert any("langsmith" in r for r in result.requirements)

    def test_merger_safety_policies(self):
        """Test that regex is included when safety policies are enabled."""
        merger = DependencyMerger(
            framework="custom",
            has_safety_policies=True,
        )
        result = merger.merge()

        assert any("regex" in r for r in result.requirements)

    def test_merger_generate_content(self):
        """Test generating requirements.txt content."""
        merger = DependencyMerger(framework="langgraph")
        content = merger.generate_requirements_content()

        assert "pydantic" in content
        assert "langgraph" in content
        assert "# " in content  # Should have comments


class TestMergeDependencies:
    """Tests for the convenience function."""

    def test_merge_dependencies_basic(self):
        """Test basic merge using convenience function."""
        result = merge_dependencies(framework="langchain")

        assert len(result.requirements) > 0
        assert any("langchain" in r for r in result.requirements)


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_requirements_file(self):
        """Test handling empty requirements file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("# Only comments\n")
            f.write("   \n")
            f.flush()

            reqs = parse_requirements_file(Path(f.name))
            assert len(reqs) == 0

    def test_duplicate_requirements_merged(self):
        """Test that duplicate requirements are merged."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("pydantic>=2.5.0\n")
            f.write("pydantic>=2.6.0\n")  # Duplicate with different version
            f.flush()

            merger = DependencyMerger(framework="custom")
            result = merger.merge(user_requirements_file=Path(f.name))

            # Should only have one pydantic entry
            pydantic_entries = [r for r in result.requirements if "pydantic" in r.lower()]
            assert len(pydantic_entries) == 1

    def test_package_name_normalization(self):
        """Test that package names are normalized."""
        # langchain_core, langchain-core, and Langchain-Core should all match
        req1 = parse_requirement("langchain_core>=0.1.0")
        req2 = parse_requirement("langchain-core>=0.1.0")
        req3 = parse_requirement("Langchain-Core>=0.1.0")

        assert req1 is not None
        assert req2 is not None
        assert req3 is not None

        assert req1.normalized_name == req2.normalized_name == req3.normalized_name

    def test_version_constraint_string_representation(self):
        """Test string representation of constraints."""
        c = parse_version_constraint(">=2.5.0")
        assert str(c) == ">=2.5.0"

    def test_requirement_to_pip_string(self):
        """Test converting requirement to pip string."""
        req = parse_requirement("uvicorn[standard]>=0.27.0")
        assert req is not None
        pip_str = req.to_pip_string()
        assert "uvicorn" in pip_str
        assert "standard" in pip_str
        assert ">=" in pip_str

    def test_conflict_error_has_hints(self):
        """Test that DependencyConflictError includes resolution hints."""
        resolver = VersionResolver()
        req = parse_requirement("pydantic==1.0.0")
        assert req is not None

        try:
            resolver.resolve(req)
            pytest.fail("Expected DependencyConflictError")
        except DependencyConflictError as e:
            assert len(e.resolution_hints) > 0
            assert e.package == "pydantic"


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for the complete dependency workflow."""

    def test_full_workflow_langgraph(self):
        """Test complete workflow for a LangGraph project."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("# My project dependencies\n")
            f.write("langchain-openai>=0.1.0\n")
            f.write("langchain-anthropic>=0.1.0\n")
            f.write("python-dotenv>=1.0.0\n")
            f.flush()

            result = merge_dependencies(
                framework="langgraph",
                user_requirements_file=Path(f.name),
                observability={"langfuse": True},
            )

            # Check core deps
            assert any("pydantic" in r for r in result.requirements)
            assert any("fastapi" in r for r in result.requirements)

            # Check framework deps
            assert any("langgraph" in r for r in result.requirements)
            assert any("langchain" in r for r in result.requirements)

            # Check user deps
            assert any("langchain-openai" in r for r in result.requirements)
            assert any("langchain-anthropic" in r for r in result.requirements)
            assert any("python-dotenv" in r for r in result.requirements)

            # Check observability
            assert any("langfuse" in r for r in result.requirements)

    def test_full_workflow_custom_framework(self):
        """Test complete workflow for a custom framework project."""
        result = merge_dependencies(
            framework="custom",
            extra_dependencies=["my-custom-lib>=1.0.0"],
        )

        # Should have core deps but no framework deps
        assert any("pydantic" in r for r in result.requirements)
        assert any("my-custom-lib" in r for r in result.requirements)
        assert not any("langgraph" in r for r in result.requirements)


# ============================================================================
# Dockrion Meta-Package Inclusion Tests
# ============================================================================


class TestDockrionMetaPackageInclusion:
    """Tests to verify dockrion meta-package is always included in merged requirements."""

    def test_dockrion_included_when_no_user_requirements(self):
        """Test that dockrion is included when there are no user requirements."""
        merger = DependencyMerger(framework="langgraph")
        result = merger.merge()

        # Should have dockrion meta-package
        dockrion_entries = [r for r in result.requirements if r.startswith("dockrion")]
        assert len(dockrion_entries) == 1
        assert "dockrion>=" in dockrion_entries[0]

    def test_dockrion_included_with_user_requirements(self):
        """Test that dockrion is included alongside user requirements."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("requests>=2.28.0\n")
            f.write("pandas>=2.0.0\n")
            f.flush()

            merger = DependencyMerger(framework="langchain")
            result = merger.merge(user_requirements_file=Path(f.name))

            # Should have dockrion meta-package
            dockrion_entries = [r for r in result.requirements if r.startswith("dockrion")]
            assert len(dockrion_entries) == 1

            # Should also have user requirements
            assert any("pandas" in r for r in result.requirements)
            assert any("requests" in r for r in result.requirements)

    def test_user_can_override_dockrion_version(self):
        """Test that user can specify their own dockrion version."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("dockrion==0.0.5\n")  # User specifies exact version
            f.flush()

            merger = DependencyMerger(framework="langgraph")
            result = merger.merge(user_requirements_file=Path(f.name))

            # Should have exactly one dockrion entry - the user's version
            dockrion_entries = [r for r in result.requirements if r.startswith("dockrion")]
            assert len(dockrion_entries) == 1
            assert "dockrion==0.0.5" in dockrion_entries[0]

    def test_dockrion_in_resolution_details(self):
        """Test that dockrion appears in resolution details."""
        merger = DependencyMerger(framework="custom")
        result = merger.merge()

        # Should have dockrion in resolutions
        assert "dockrion" in result.resolutions

    def test_dockrion_included_via_extra_dependencies(self):
        """Test that user-specified dockrion in extra_dependencies is respected."""
        merger = DependencyMerger(framework="langgraph")
        result = merger.merge(extra_dependencies=["dockrion>=0.1.0"])

        # Should have exactly one dockrion entry
        dockrion_entries = [r for r in result.requirements if r.startswith("dockrion")]
        assert len(dockrion_entries) == 1
        # User's version should be used
        assert "0.1.0" in dockrion_entries[0]

    def test_merge_dependencies_convenience_function_includes_dockrion(self):
        """Test that the convenience function also includes dockrion."""
        result = merge_dependencies(framework="langchain")

        # Should have dockrion meta-package
        dockrion_entries = [r for r in result.requirements if r.startswith("dockrion")]
        assert len(dockrion_entries) == 1

    def test_dockrion_not_duplicated_with_extras(self):
        """Test that dockrion is not duplicated when user specifies with extras."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("dockrion[langgraph]>=0.0.2\n")
            f.flush()

            merger = DependencyMerger(framework="langgraph")
            result = merger.merge(user_requirements_file=Path(f.name))

            # Should have exactly one dockrion entry
            dockrion_entries = [r for r in result.requirements if r.startswith("dockrion")]
            assert len(dockrion_entries) == 1
            # User's extras should be preserved
            assert "langgraph" in dockrion_entries[0]


# ============================================================================
# PyProject.toml Utilities Tests (Single Source of Truth)
# ============================================================================


class TestPyProjectUtilities:
    """Tests for pyproject.toml reading utilities."""

    def test_get_dockrion_version(self):
        """Test that dockrion version is read from pyproject.toml."""
        from dockrion_sdk.utils.workspace import get_dockrion_version

        version = get_dockrion_version()
        # Should return a valid version string
        assert version is not None
        assert isinstance(version, str)
        # Version should match semver-like pattern
        assert "." in version or version == "0.0.1"  # fallback

    def test_get_core_dependencies_from_pyproject(self):
        """Test that core dependencies are read from pyproject.toml."""
        from dockrion_sdk.utils.workspace import get_core_dependencies_from_pyproject

        deps = get_core_dependencies_from_pyproject()
        # Should return a dict (may be empty if pyproject.toml not found)
        assert isinstance(deps, dict)
        # If we're in the workspace, should have pydantic
        if deps:
            assert "pydantic" in deps

    def test_get_runtime_dependencies_from_pyproject(self):
        """Test that runtime dependencies are read from pyproject.toml."""
        from dockrion_sdk.utils.workspace import get_runtime_dependencies_from_pyproject

        deps = get_runtime_dependencies_from_pyproject()
        # Should return a dict
        assert isinstance(deps, dict)
        # If we're in the workspace, should have fastapi
        if deps:
            assert "fastapi" in deps

    def test_get_framework_dependencies_from_pyproject(self):
        """Test that framework dependencies are read from pyproject.toml."""
        from dockrion_sdk.utils.workspace import get_framework_dependencies_from_pyproject

        # Test langgraph
        deps = get_framework_dependencies_from_pyproject("langgraph")
        assert isinstance(deps, dict)
        if deps:
            assert "langgraph" in deps or "langchain-core" in deps

        # Test langchain
        deps = get_framework_dependencies_from_pyproject("langchain")
        assert isinstance(deps, dict)
        if deps:
            assert "langchain" in deps or "langchain-core" in deps

    def test_dependencies_used_in_resolver_match_pyproject(self):
        """Test that resolver uses dependencies from pyproject.toml."""
        from dockrion_sdk.dependencies.resolver import CORE_DEPENDENCIES
        from dockrion_sdk.utils.workspace import get_core_dependencies_from_pyproject

        pyproject_deps = get_core_dependencies_from_pyproject()
        if pyproject_deps:
            # Core dependencies should match pyproject.toml
            for pkg in pyproject_deps:
                assert pkg in CORE_DEPENDENCIES

    def test_dockrion_meta_package_uses_correct_version(self):
        """Test that DOCKRION_META_PACKAGE uses version from pyproject.toml."""
        from dockrion_sdk.dependencies.merger import DOCKRION_META_PACKAGE
        from dockrion_sdk.utils.workspace import get_dockrion_version

        version = get_dockrion_version()
        expected = f"dockrion>={version}"
        assert DOCKRION_META_PACKAGE == expected

    def test_clear_pyproject_cache(self):
        """Test that cache can be cleared."""
        from dockrion_sdk.utils.workspace import (
            clear_pyproject_cache,
            get_dockrion_pyproject,
        )

        # First call caches the result
        _ = get_dockrion_pyproject()

        # Clear cache
        clear_pyproject_cache()

        # Second call should still work
        result = get_dockrion_pyproject()
        assert isinstance(result, dict)
