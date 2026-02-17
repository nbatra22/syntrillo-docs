# sources/syntrillo/stroke_risk_score_v3/architecture.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# ============================================================================
# 1. DATA LAYER - Fetch raw data from sources
# ============================================================================

class DataSource(ABC):
    """Abstract base for all data sources"""

    @abstractmethod
    def fetch(self) -> Dict[str, Any]:
        """Fetch raw data from this source"""
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Identifier for this data source"""
        pass


class TenoviBPDataSource(DataSource):
    """Fetches blood pressure data from Tenovi"""

    def __init__(self, syntrillo_internal_key: uuid.UUID):
        self.syntrillo_internal_key = syntrillo_internal_key
        self.bp_analysis = BloodPressureAnalysis(syntrillo_internal_key)

    def fetch(self) -> Dict[str, Any]:
        """Returns raw BP dataframe and metadata"""
        bp_df, metadata = self.bp_analysis.get_blood_pressure_dataframe()
        return {
            "dataframe": bp_df,
            "metadata": metadata,
            "baseline_start": bp_df[TIMESTAMP_LOCAL].min() if bp_df is not None else None
        }

    @property
    def source_name(self) -> str:
        return "tenovi_bp"


class HealthieMetricsDataSource(DataSource):
    """Fetches RHR, activity, lab values from Healthie"""

    def __init__(self, healthie_user_id: str, healthie_utils: HealthieUtils):
        self.healthie_user_id = healthie_user_id
        self.healthie_utils = healthie_utils

    def fetch(self) -> Dict[str, Any]:
        """Returns all Healthie metric data"""
        return {
            "rhr_data": self._fetch_metric(RHR_CATEGORY),
            "activity_data": self._fetch_activity_data(),
            "lab_data": self._fetch_lab_data()
        }

    def _fetch_metric(self, category: str) -> List[dict]:
        # Implementation...
        pass

    @property
    def source_name(self) -> str:
        return "healthie_metrics"


class SRSFormDataSource(DataSource):
    """Fetches patient medical history from SRS forms"""

    def __init__(self, syntrillo_internal_key: uuid.UUID, db_manager):
        self.syntrillo_internal_key = syntrillo_internal_key
        self.db_manager = db_manager

    def fetch(self) -> Dict[str, Any]:
        """Returns most recent SRS form response"""
        responses = self.db_manager.get_srs_form_responses(self.syntrillo_internal_key)
        return {
            "form_response": responses[0] if responses else None
        }

    @property
    def source_name(self) -> str:
        return "srs_form"


class DataFetcher:
    """Orchestrates fetching from multiple data sources"""

    def __init__(self, data_sources: List[DataSource]):
        self.data_sources = data_sources

    def fetch_all(self) -> Dict[str, Any]:
        """Fetch from all sources, track success/failure"""
        results = {}
        metadata = {
            "queries_attempted": len(self.data_sources),
            "queries_successful": 0,
            "missing_sources": []
        }

        for source in self.data_sources:
            try:
                results[source.source_name] = source.fetch()
                metadata["queries_successful"] += 1
            except Exception as e:
                logger.error(f"Failed to fetch from {source.source_name}: {e}")
                results[source.source_name] = None
                metadata["missing_sources"].append(source.source_name)

        results["_fetch_metadata"] = metadata
        return results

    async def fetch_all_async(self) -> Dict[str, Any]:
        """Fetch from all sources in parallel"""
        tasks = [
            asyncio.to_thread(source.fetch)
            for source in self.data_sources
        ]

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        metadata = {
            "queries_attempted": len(self.data_sources),
            "queries_successful": 0,
            "missing_sources": []
        }

        for source, result in zip(self.data_sources, results_list):
            if isinstance(result, Exception):
                results[source.source_name] = None
                metadata["missing_sources"].append(source.source_name)
            else:
                results[source.source_name] = result
                metadata["queries_successful"] += 1

        results["_fetch_metadata"] = metadata
        return results


# ============================================================================
# 2. CALCULATION LAYER - Compute risk values and contributions
# ============================================================================

@dataclass
class RiskValue:
    """Represents a calculated risk value"""
    raw: Optional[float]
    unit: Optional[str]
    risk_level: str  # low, low_intermediate, intermediate_high, high
    threshold_info: Optional[Dict[str, Any]] = None


@dataclass
class Contribution:
    """Represents contribution to SRS/SPS scores"""
    srs_absolute: float
    sps_absolute: float
    srs_percentage: float
    sps_percentage: float
    weight_applied: Optional[float] = None


class MetricCalculator(ABC):
    """Base class for calculating risk metrics"""

    @abstractmethod
    def calculate(self, raw_data: Dict[str, Any]) -> RiskValue:
        """Calculate risk value from raw data"""
        pass

    @abstractmethod
    def calculate_contribution(self, risk_value: RiskValue) -> Contribution:
        """Calculate contribution to total scores"""
        pass

    @property
    @abstractmethod
    def metric_id(self) -> str:
        pass


class BPMetricCalculator(MetricCalculator):
    """Calculates BP-related metrics and contributions"""

    def __init__(self, metric_type: str, timeframe: str, weighting: dict):
        # metric_type: "avg_sbp", "sbp_std", "avg_dbp", etc.
        # timeframe: "trailing", "baseline", "prior"
        self.metric_type = metric_type
        self.timeframe = timeframe
        self.weighting = weighting

    @property
    def metric_id(self) -> str:
        return f"{self.metric_type}_{self.timeframe}"

    def calculate(self, raw_data: Dict[str, Any]) -> RiskValue:
        """Extract and compute BP metric"""
        bp_df = raw_data["dataframe"]
        baseline_start = raw_data["baseline_start"]

        # Get timeframed data
        if self.timeframe == "trailing":
            df = self._get_trailing_df(bp_df, baseline_start)
        elif self.timeframe == "baseline":
            df = self._get_baseline_df(bp_df, baseline_start)

        # Calculate metric
        if self.metric_type == "avg_sbp":
            value = df["sbp"].mean() if not df.empty else None
            return RiskValue(
                raw=value,
                unit="mmHg",
                risk_level=self._categorize_sbp(value) if value else "unknown"
            )
        elif self.metric_type == "sbp_std":
            value = df["sbp"].std() if not df.empty else None
            return RiskValue(
                raw=value,
                unit="mmHg (std dev)",
                risk_level=self._categorize_sbp_variability(value) if value else "unknown"
            )
        # ... other metric types

    def calculate_contribution(self, risk_value: RiskValue) -> Contribution:
        """Map risk value to contribution using weighting"""
        if risk_value.raw is None:
            return Contribution(0, 0, 0, 0, None)

        # Apply weighting based on risk level
        weight = self.weighting[VALUE][risk_value.risk_level]
        base_contribution = self._get_base_contribution(self.metric_type)

        srs_absolute = base_contribution * weight
        sps_absolute = base_contribution * weight  # Could differ for SPS

        return Contribution(
            srs_absolute=srs_absolute,
            sps_absolute=sps_absolute,
            srs_percentage=0,  # Calculated later when total is known
            sps_percentage=0,
            weight_applied=weight
        )

    def _categorize_sbp(self, sbp: float) -> str:
        if sbp < 120: return "low"
        elif sbp < 130: return "low_intermediate"
        elif sbp < 140: return "intermediate_high"
        else: return "high"

    def _get_trailing_df(self, bp_df, baseline_start):
        # Implementation...
        pass


class HealthieMetricCalculator(MetricCalculator):
    """Calculates Healthie-based metrics (RHR, inactivity, etc.)"""

    def __init__(self, metric_type: str, weighting: dict):
        self.metric_type = metric_type  # "rhr", "physical_inactivity", etc.
        self.weighting = weighting

    @property
    def metric_id(self) -> str:
        return self.metric_type

    def calculate(self, raw_data: Dict[str, Any]) -> RiskValue:
        if self.metric_type == "rhr":
            rhr_data = raw_data["rhr_data"]
            # Calculate trailing average
            trailing_avg = self._calculate_rhr_trailing(rhr_data)
            return RiskValue(
                raw=trailing_avg,
                unit="bpm",
                risk_level=self._categorize_rhr(trailing_avg) if trailing_avg else "unknown"
            )
        elif self.metric_type == "physical_inactivity":
            activity_data = raw_data["activity_data"]
            hours = activity_data.get("inactivity_hours_answer")
            return RiskValue(
                raw=hours,
                unit="hours/day",
                risk_level=self._categorize_inactivity(hours) if hours else "unknown"
            )

    def calculate_contribution(self, risk_value: RiskValue) -> Contribution:
        # Similar to BP calculator
        pass


class MedicalHistoryCalculator(MetricCalculator):
    """Calculates dependent risk factors from medical history"""

    def __init__(self, condition: str, weighting: dict):
        self.condition = condition  # "cad", "afib", "stroke", etc.
        self.weighting = weighting

    @property
    def metric_id(self) -> str:
        return self.condition

    def calculate(self, raw_data: Dict[str, Any]) -> RiskValue:
        form_response = raw_data["form_response"]

        if self.condition == "cad":
            if not form_response.HistoryOfCAD:
                return RiskValue(raw=None, unit=None, risk_level="none")

            cad_type = form_response.CADType.value if form_response.CADType else None
            return RiskValue(
                raw=cad_type,
                unit=None,
                risk_level=self._categorize_cad(form_response.CADType)
            )

    def calculate_contribution(self, risk_value: RiskValue, compliance_status: str) -> Contribution:
        """Dependent factors consider treatment compliance"""
        if risk_value.risk_level == "none":
            return Contribution(0, 0, 0, 0)

        base_risk = self.weighting[VALUE][risk_value.risk_level]
        efficacy = self.weighting[TREATMENT_EFFICACY].get(HIGH_EFFICACY, 0)
        optimization = self.weighting[TREATMENT_OPTIM].get(compliance_status, 0)

        # Dependent formula: ((base-1)*(1-(efficacy*optimization)))+1
        section_score = ((base_risk - 1) * (1 - (efficacy * optimization))) + 1

        return Contribution(
            srs_absolute=section_score,
            sps_absolute=section_score,
            srs_percentage=0,  # Calculated later
            sps_percentage=0
        )


# ============================================================================
# 3. BUILDER LAYER - Construct normalized risk factor objects
# ============================================================================

@dataclass
class TimeframeInfo:
    """Metadata about a timeframe"""
    type: str  # "trailing", "baseline", "prior"
    duration_weeks: int
    measurement_count: Optional[int] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None


@dataclass
class RiskFactor:
    """Normalized risk factor object"""
    id: str
    display_name: str
    category: str  # "independent" or "dependent"
    tags: List[str]
    source: str
    timeframe: Optional[TimeframeInfo]
    value: RiskValue
    contribution: Contribution
    related_metrics: Optional[List[str]] = None
    compliance: Optional[Dict[str, Any]] = None
    data_quality: Optional[Dict[str, Any]] = None


class RiskFactorBuilder(ABC):
    """Base class for building risk factor objects"""

    @abstractmethod
    def build(self, raw_data: Dict[str, Any], calculator: MetricCalculator) -> Optional[RiskFactor]:
        """Build a risk factor object"""
        pass


class IndependentRiskFactorBuilder(RiskFactorBuilder):
    """Builds independent risk factors"""

    DISPLAY_NAMES = {
        "avg_sbp_trailing": "Average Systolic BP (Trailing)",
        "avg_sbp_baseline": "Average Systolic BP (Baseline)",
        "sbp_std_trailing": "Systolic BP Variability",
        "rhr": "Resting Heart Rate",
        "physical_inactivity": "Physical Inactivity",
    }

    TAGS = {
        "avg_sbp_trailing": ["blood_pressure", "cardiovascular", "tenovi", "objective"],
        "sbp_std_trailing": ["blood_pressure", "cardiovascular", "tenovi", "objective"],
        "rhr": ["cardiovascular", "healthie", "objective"],
        "physical_inactivity": ["lifestyle", "activity", "healthie", "subjective"],
    }

    def build(self, raw_data: Dict[str, Any], calculator: MetricCalculator) -> Optional[RiskFactor]:
        """Build an independent risk factor"""
        metric_id = calculator.metric_id

        # Calculate value and contribution
        risk_value = calculator.calculate(raw_data)
        contribution = calculator.calculate_contribution(risk_value)

        # Decide if we should include this metric
        if not self._should_include(metric_id, risk_value):
            return None

        # Build timeframe info if applicable
        timeframe = self._build_timeframe(metric_id, raw_data)

        return RiskFactor(
            id=metric_id,
            display_name=self.DISPLAY_NAMES.get(metric_id, metric_id),
            category="independent",
            tags=self.TAGS.get(metric_id, []),
            source=self._determine_source(metric_id),
            timeframe=timeframe,
            value=risk_value,
            contribution=contribution,
            related_metrics=self._get_related_metrics(metric_id),
            data_quality=self._assess_data_quality(risk_value) if risk_value.raw is None else None
        )

    def _should_include(self, metric_id: str, risk_value: RiskValue) -> bool:
        """Decide if metric should be included when value is None"""
        ALWAYS_INCLUDE = ["avg_sbp_trailing", "rhr", "physical_inactivity"]
        EXCLUDE_IF_NULL = ["substance_use", "ssq_score"]

        if risk_value.raw is not None:
            return True
        return metric_id in ALWAYS_INCLUDE and metric_id not in EXCLUDE_IF_NULL

    def _build_timeframe(self, metric_id: str, raw_data: Dict[str, Any]) -> Optional[TimeframeInfo]:
        """Build timeframe info for metrics that have it"""
        if "trailing" in metric_id:
            return TimeframeInfo(
                type="trailing",
                duration_weeks=4,
                # Could extract actual dates from raw_data
            )
        elif "baseline" in metric_id:
            return TimeframeInfo(
                type="baseline",
                duration_weeks=2,
            )
        return None

    def _determine_source(self, metric_id: str) -> str:
        if "sbp" in metric_id or "dbp" in metric_id:
            return "tenovi"
        elif "rhr" in metric_id or "inactivity" in metric_id:
            return "healthie"
        elif "ldl" in metric_id or "creatinine" in metric_id:
            return "healthie_labs"
        return "unknown"

    def _get_related_metrics(self, metric_id: str) -> Optional[List[str]]:
        RELATIONSHIPS = {
            "avg_sbp_trailing": ["sbp_std_trailing", "avg_peak_sbp_trailing"],
            "sbp_std_trailing": ["avg_sbp_trailing"],
        }
        return RELATIONSHIPS.get(metric_id)

    def _assess_data_quality(self, risk_value: RiskValue) -> Dict[str, Any]:
        return {
            "available": False,
            "reason": "no_measurements"
        }


class DependentRiskFactorBuilder(RiskFactorBuilder):
    """Builds dependent risk factors"""

    DISPLAY_NAMES = {
        "cad": "Coronary Artery Disease",
        "afib": "Atrial Fibrillation",
        "stroke": "Previous Stroke",
        "ldl": "LDL Cholesterol",
    }

    def build(self, raw_data: Dict[str, Any], calculator: MetricCalculator) -> Optional[RiskFactor]:
        """Build a dependent risk factor"""
        metric_id = calculator.metric_id
        form_response = raw_data["form_response"]

        # Calculate value
        risk_value = calculator.calculate(raw_data)

        # Don't include if condition doesn't exist
        if risk_value.risk_level == "none":
            return None

        # Get compliance status
        compliance_status = self._get_compliance_status(metric_id, form_response)

        # Calculate contribution with compliance
        contribution = calculator.calculate_contribution(risk_value, compliance_status)

        return RiskFactor(
            id=metric_id,
            display_name=self.DISPLAY_NAMES.get(metric_id, metric_id),
            category="dependent",
            tags=["medical_history", "subjective"],
            source="srs_form",
            timeframe=None,
            value=risk_value,
            contribution=contribution,
            compliance={"status": compliance_status} if compliance_status else None
        )

    def _get_compliance_status(self, metric_id: str, form_response) -> Optional[str]:
        if not form_response or not form_response.compliance:
            return None

        compliance_mapping = {
            "cad": "cadCompliance",
            "ldl": "ldlCompliance",
            "afib": "atrialFibrillationCompliance",
        }

        attr_name = compliance_mapping.get(metric_id)
        if attr_name:
            compliance_obj = getattr(form_response.compliance, attr_name, None)
            return compliance_obj.value if compliance_obj else None
        return None


# ============================================================================
# 4. ORCHESTRATION LAYER - Assemble final response
# ============================================================================

class SRSResponseBuilder:
    """Builds the complete normalized SRS response"""

    def __init__(self, syntrillo_internal_key: uuid.UUID):
        self.syntrillo_internal_key = syntrillo_internal_key
        self.start_time = time.time()
        self.risk_factors: List[RiskFactor] = []

    def add_risk_factor(self, risk_factor: Optional[RiskFactor]):
        """Add a risk factor to the response"""
        if risk_factor is not None:
            self.risk_factors.append(risk_factor)

    def calculate_percentages(self):
        """Calculate percentage contributions after all factors are added"""
        # Calculate totals
        total_srs = sum(rf.contribution.srs_absolute for rf in self.risk_factors)
        total_sps = sum(rf.contribution.sps_absolute for rf in self.risk_factors)

        # Update percentages
        for rf in self.risk_factors:
            if total_srs > 0:
                rf.contribution.srs_percentage = round(
                    (rf.contribution.srs_absolute / total_srs) * 100, 1
                )
            if total_sps > 0:
                rf.contribution.sps_percentage = round(
                    (rf.contribution.sps_absolute / total_sps) * 100, 1
                )

    def build(self, final_srs: float, final_sps: float, fetch_metadata: dict) -> dict:
        """Build final response object"""
        self.calculate_percentages()

        return {
            "metadata": self._build_metadata(fetch_metadata),
            "scores": {
                "srs": final_srs,
                "sps": final_sps
            },
            "risk_factors": [self._risk_factor_to_dict(rf) for rf in self.risk_factors],
            "summary": self._build_summary()
        }

    def _build_metadata(self, fetch_metadata: dict) -> dict:
        return {
            "patient_id": str(self.syntrillo_internal_key),
            "calculated_at": datetime.now().isoformat(),
            "calculation_duration_ms": int((time.time() - self.start_time) * 1000),
            "data_completeness": fetch_metadata
        }

    def _build_summary(self) -> dict:
        """Build summary statistics"""
        summary = {
            "by_category": {},
            "by_tag": {},
            "top_contributors": []
        }

        # By category
        for category in ["independent", "dependent"]:
            category_factors = [rf for rf in self.risk_factors if rf.category == category]
            summary["by_category"][category] = {
                "srs_contribution": sum(rf.contribution.srs_absolute for rf in category_factors),
                "sps_contribution": sum(rf.contribution.sps_absolute for rf in category_factors),
                "metric_count": len(category_factors)
            }

        # By tag
        all_tags = set()
        for rf in self.risk_factors:
            all_tags.update(rf.tags)

        for tag in all_tags:
            tag_factors = [rf for rf in self.risk_factors if tag in rf.tags]
            summary["by_tag"][tag] = {
                "srs_contribution": sum(rf.contribution.srs_absolute for rf in tag_factors),
                "metric_count": len(tag_factors)
            }

        # Top contributors
        sorted_factors = sorted(
            self.risk_factors,
            key=lambda x: x.contribution.srs_absolute,
            reverse=True
        )
        summary["top_contributors"] = [
            {"id": rf.id, "srs_contribution": rf.contribution.srs_absolute}
            for rf in sorted_factors[:5]
        ]

        return summary

    def _risk_factor_to_dict(self, rf: RiskFactor) -> dict:
        """Convert RiskFactor to dictionary"""
        result = {
            "id": rf.id,
            "display_name": rf.display_name,
            "category": rf.category,
            "tags": rf.tags,
            "source": rf.source,
            "timeframe": asdict(rf.timeframe) if rf.timeframe else None,
            "value": {
                "raw": rf.value.raw,
                "unit": rf.value.unit,
                "risk_level": rf.value.risk_level,
                "threshold_info": rf.value.threshold_info
            },
            "contribution": {
                "srs_absolute": rf.contribution.srs_absolute,
                "sps_absolute": rf.contribution.sps_absolute,
                "srs_percentage": rf.contribution.srs_percentage,
                "sps_percentage": rf.contribution.sps_percentage,
            }
        }

        if rf.contribution.weight_applied:
            result["contribution"]["weight_applied"] = rf.contribution.weight_applied

        if rf.related_metrics:
            result["related_metrics"] = rf.related_metrics

        if rf.compliance:
            result["compliance"] = rf.compliance

        if rf.data_quality:
            result["data_quality"] = rf.data_quality

        return result


# ============================================================================
# 5. MAIN ORCHESTRATOR - Ties everything together
# ============================================================================

class SRSEngine:
    """Main engine that orchestrates the entire SRS calculation"""

    def __init__(self, syntrillo_internal_key: uuid.UUID):
        self.syntrillo_internal_key = syntrillo_internal_key
        self.weighting = {
            VALUE: {
                LOW_VALUE: 1.25,
                LOW_INTERMEDIATE_VALUE: 1.50,
                INTERMEDIATE_HIGH_VALUE: 1.75,
                HIGH_VALUE: 2.25,
            },
            TREATMENT_EFFICACY: {
                MODERATE_EFFICACY: 0.35,
                HIGH_EFFICACY: 0.70,
            },
            TREATMENT_OPTIM: {
                TreatmentComplianceOptions.OPTIMIZED: 1.0,
                TreatmentComplianceOptions.PARTIALLY_OPTIMIZED: 0.5,
                TreatmentComplianceOptions.NOT_OPTIMIZED: 0.0,
            }
        }

    def calculate(self, is_ondemand_srs: bool = False) -> dict:
        """Main entry point - calculates SRS and returns normalized response"""

        # 1. Fetch all data
        data_sources = self._build_data_sources()
        fetcher = DataFetcher(data_sources)
        raw_data = fetcher.fetch_all()

        # 2. Initialize response builder
        response_builder = SRSResponseBuilder(self.syntrillo_internal_key)

        # 3. Build all independent risk factors
        independent_calculators = self._build_independent_calculators()
        independent_builder = IndependentRiskFactorBuilder()

        for calculator in independent_calculators:
            risk_factor = independent_builder.build(raw_data, calculator)
            response_builder.add_risk_factor(risk_factor)

        # 4. Build all dependent risk factors
        dependent_calculators = self._build_dependent_calculators()
        dependent_builder = DependentRiskFactorBuilder()

        for calculator in dependent_calculators:
            risk_factor = dependent_builder.build(raw_data, calculator)
            response_builder.add_risk_factor(risk_factor)

        # 5. Calculate final scores
        final_srs, final_sps = self._calculate_final_scores(response_builder.risk_factors)

        # 6. Build and return normalized response
        return response_builder.build(final_srs, final_sps, raw_data["_fetch_metadata"])

    async def calculate_async(self, is_ondemand_srs: bool = False) -> dict:
        """Async version with parallel data fetching"""
        # 1. Fetch all data in parallel
        data_sources = self._build_data_sources()
        fetcher = DataFetcher(data_sources)
        raw_data = await fetcher.fetch_all_async()

        # Rest is same as sync version...
        # (calculations are CPU-bound, not I/O-bound, so no benefit to async)

    def _build_data_sources(self) -> List[DataSource]:
        """Build all data sources"""
        # Get healthie_user_id
        lookup_codes = LookUpCodesManagement()
        entry = lookup_codes.retrieve_entry_by_internal_key(self.syntrillo_internal_key)
        healthie_user_id = entry.get('healthie_user_id') if entry else None

        healthie_utils = HealthieUtils()

        return [
            TenoviBPDataSource(self.syntrillo_internal_key),
            HealthieMetricsDataSource(healthie_user_id, healthie_utils),
            SRSFormDataSource(self.syntrillo_internal_key, SyntrilloDatabaseManager(self.syntrillo_internal_key))
        ]

    def _build_independent_calculators(self) -> List[MetricCalculator]:
        """Build calculators for all independent metrics"""
        return [
            BPMetricCalculator("avg_sbp", "trailing", self.weighting),
            BPMetricCalculator("avg_sbp", "baseline", self.weighting),
            BPMetricCalculator("sbp_std", "trailing", self.weighting),
            BPMetricCalculator("avg_peak_sbp", "trailing", self.weighting),
            BPMetricCalculator("avg_dbp", "trailing", self.weighting),
            HealthieMetricCalculator("rhr", self.weighting),
            HealthieMetricCalculator("physical_inactivity", self.weighting),
            # ... more calculators
        ]

    def _build_dependent_calculators(self) -> List[MetricCalculator]:
        """Build calculators for all dependent metrics"""
        return [
            MedicalHistoryCalculator("cad", self.weighting),
            MedicalHistoryCalculator("afib", self.weighting),
            MedicalHistoryCalculator("stroke", self.weighting),
            # ... more calculators
        ]

    def _calculate_final_scores(self, risk_factors: List[RiskFactor]) -> tuple[float, float]:
        """Calculate final SRS and SPS scores"""
        independent_srs = 1.0
        independent_sps = 1.0
        dependent_score = 1.0

        for rf in risk_factors:
            if rf.category == "independent":
                independent_srs *= rf.contribution.srs_absolute
                independent_sps *= rf.contribution.sps_absolute
            else:  # dependent
                dependent_score *= rf.contribution.srs_absolute

        total_srs = dependent_score * independent_srs
        total_sps = dependent_score * independent_sps

        final_srs = round(total_srs ** 0.70, 2)
        final_sps = round(total_sps ** 0.70, 2)

        return final_srs, final_sps


# ============================================================================
# 6. USAGE
# ============================================================================

if __name__ == "__main__":
# Simple sync usage

    syntrillo_internal_key = "your_internal_key_here"

    # Simple sync usage
    engine = SRSEngine(syntrillo_internal_key)
    response = engine.calculate()
    print(response)

    # Async usage with parallel fetching
    async def main():
        response = await engine.calculate_async()
        print(response)


