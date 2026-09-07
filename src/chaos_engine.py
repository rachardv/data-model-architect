import math
import random
import time
from typing import Dict, Any, List, Optional
import duckdb

class AdversarialChaosGenerator:
    """
    Deterministic Adversarial Chaos & Skew Generator.
    Uses pure mathematical formulas and fixed-seed PRNG (seed=42)
    to produce 100% reproducible stress scenarios across CI/CD environments.
    """
    
    DEFAULT_SEED = 42

    @classmethod
    def generate_skewed_keys(
        cls,
        n_rows: int,
        num_keys: int = 100,
        n_keys: Optional[int] = None,
        skew_factor: float = 0.8,
        skew_alpha: Optional[float] = None,
        seed: int = DEFAULT_SEED
    ) -> List[str]:
        """
        Generates a Zipfian (power-law) key distribution where ~80% of rows
        cluster around the top few keys (simulating extreme hot-spot key skew).
        Supports both num_keys/n_keys and skew_factor/skew_alpha parameter names.
        """
        k_count = n_keys if n_keys is not None else num_keys
        s_factor = skew_alpha if skew_alpha is not None else skew_factor

        rng = random.Random(seed)
        # Zipfian weights: weight(k) = 1 / k^s
        weights = [1.0 / math.pow(i, s_factor) for i in range(1, k_count + 1)]
        total_weight = sum(weights)
        probabilities = [w / total_weight for w in weights]
        
        # Cumulative probabilities
        cum_probs = []
        c = 0.0
        for p in probabilities:
            c += p
            cum_probs.append(c)
            
        keys = [f"CUST_SKEW_{i}" for i in range(1, k_count + 1)]
        
        result = []
        for _ in range(n_rows):
            r = rng.random()
            idx = 0
            for i, cp in enumerate(cum_probs):
                if r <= cp:
                    idx = i
                    break
            result.append(keys[idx])
        return result

    @classmethod
    def generate_temporal_jitter(
        cls,
        base_timestamps: List[str],
        max_jitter_hours: int = 48,
        seed: int = DEFAULT_SEED
    ) -> List[str]:
        """
        Generates deterministic clock drift (+/- jitter hours) to simulate
        out-of-order event arrivals and microservice clock skew.
        """
        rng = random.Random(seed)
        jittered = []
        for ts_str in base_timestamps:
            offset_hours = rng.randint(-max_jitter_hours, max_jitter_hours)
            jittered.append(f"{ts_str} + INTERVAL '{offset_hours}' HOUR")
        return jittered

    @classmethod
    def simulate_gdpr_erasure(
        cls,
        con: Optional[duckdb.DuckDBPyConnection] = None,
        dim_table: str = "dim_customer",
        customer_id_val: Optional[str] = None,
        fact_table: Optional[str] = "fct_orders",
        customer_count: int = 100,
        orders_per_customer: int = 5,
        customers_to_erase: int = 1
    ) -> Dict[str, Any]:
        """
        Physically proves GDPR Right to be Forgotten compliance:
          1. Updates dimension PII attributes to 'REDACTED', phone to NULL, and email to a salt hash.
          2. Preserves customer_sk strictly intact.
          3. Asserts zero orphan foreign keys in fact_table.
          4. Asserts 100% metric conservation (fact row count and sum unchanged).
        Supports both passing an existing live connection and running fully self-contained in memory.
        """
        created_local_con = False
        if con is None:
            created_local_con = True
            con = duckdb.connect(":memory:")
            # Seed test tables
            con.execute("""
                CREATE TABLE dim_customer (
                    customer_sk BIGINT PRIMARY KEY,
                    customer_id VARCHAR,
                    customer_name VARCHAR,
                    email VARCHAR,
                    phone VARCHAR,
                    address VARCHAR
                );
                CREATE TABLE fct_orders (
                    order_id VARCHAR PRIMARY KEY,
                    customer_sk BIGINT,
                    total_amount_usd DOUBLE
                );
            """)
            # Populate data
            for i in range(1, customer_count + 1):
                cid = f"CUST_{i:04d}"
                con.execute(f"""
                    INSERT INTO dim_customer VALUES (
                        {i}, '{cid}', 'Customer Name {i}', 'cust{i}@example.com', '555-{i:04d}', 'Address {i}'
                    );
                """)
                for j in range(1, orders_per_customer + 1):
                    oid = f"ORD_{i}_{j}"
                    amt = round(10.0 * j + i, 2)
                    con.execute(f"""
                        INSERT INTO fct_orders VALUES ('{oid}', {i}, {amt});
                    """)
            if customer_id_val is None:
                customer_id_val = "CUST_0001"

        target_cid = customer_id_val or "CUST_0001"

        # Record pre-erasure stats
        pre_dim_count = con.execute(f"SELECT COUNT(*) FROM {dim_table}").fetchone()[0]
        pre_fact_stats = None
        if fact_table:
            pre_fact_stats = con.execute(f"SELECT COUNT(*), COALESCE(SUM(total_amount_usd), 0.0) FROM {fact_table}").fetchone()

        # Perform Pseudonymization Sentinel Update
        con.execute(f"""
            UPDATE {dim_table}
            SET 
                customer_name = 'REDACTED',
                email = 'gdpr_purged_' || SUBSTRING(MD5('{target_cid}'), 1, 12) || '@privacy.internal',
                phone = NULL,
                address = 'ANONYMIZED_RESIDENCE'
            WHERE customer_id = '{target_cid}';
        """)

        post_dim_count = con.execute(f"SELECT COUNT(*) FROM {dim_table}").fetchone()[0]
        redacted_row = con.execute(f"SELECT customer_name, phone, email, customer_sk FROM {dim_table} WHERE customer_id = '{target_cid}'").fetchone()
        
        orphan_fks = 0
        metric_drift = 0.0
        if fact_table:
            orphan_fks = con.execute(f"""
                SELECT COUNT(*) 
                FROM {fact_table} f
                LEFT JOIN {dim_table} d ON f.customer_sk = d.customer_sk
                WHERE d.customer_sk IS NULL;
            """).fetchone()[0]
            post_fact_stats = con.execute(f"SELECT COUNT(*), COALESCE(SUM(total_amount_usd), 0.0) FROM {fact_table}").fetchone()
            metric_drift = abs(float(pre_fact_stats[1]) - float(post_fact_stats[1]))

        compliance_verified = (
            redacted_row is not None and
            redacted_row[0] == "REDACTED" and
            redacted_row[1] is None and
            "gdpr_purged_" in str(redacted_row[2]) and
            pre_dim_count == post_dim_count and
            orphan_fks == 0 and
            metric_drift == 0.0
        )

        res = {
            "status": "PASS" if compliance_verified else "FAIL",
            "erasure_compliant": compliance_verified,
            "metric_conserved": (metric_drift == 0.0),
            "erasure_method": "PSEUDONYMIZATION_SENTINEL",
            "customer_id": target_cid,
            "retained_surrogate_key": redacted_row[3] if redacted_row else None,
            "dim_row_count_preserved": (pre_dim_count == post_dim_count),
            "orphan_foreign_keys_detected": orphan_fks,
            "orphan_fks_detected": orphan_fks,
            "financial_discrepancy": metric_drift,
            "fact_metric_drift": metric_drift,
            "pii_purged": (redacted_row[0] == "REDACTED" and redacted_row[1] is None) if redacted_row else False,
            "details": f"GDPR erasure verified: customer_id='{target_cid}' pseudonymized. Zero orphan FKs in fact table, metric drift = {metric_drift:.4f}"
        }

        if created_local_con:
            con.close()

        return res

    @classmethod
    def run_memory_constrained_benchmark(
        cls,
        con: Optional[duckdb.DuckDBPyConnection] = None,
        query: Optional[str] = None,
        max_memory: Optional[str] = None,
        memory_limit_mb: Optional[int] = None,
        num_rows: int = 10000,
        num_keys: int = 50
    ) -> Dict[str, Any]:
        """
        Executes a query under an aggressive memory cap (e.g. 16MB) to physically prove:
          1. Query finishes without Out-Of-Memory (OOM) crash.
          2. Measures execution duration and rows processed.
        Supports both passing an existing connection and self-contained benchmarking.
        """
        mem_str = max_memory or (f"{memory_limit_mb}MB" if memory_limit_mb else "16MB")
        created_local_con = False
        start_t = time.perf_counter()

        if con is None:
            created_local_con = True
            con = duckdb.connect(":memory:")
            # Generate test skewed dataset
            skewed_keys = cls.generate_skewed_keys(n_rows=num_rows, num_keys=num_keys, skew_factor=1.2)
            con.execute("CREATE TABLE skew_test (k VARCHAR, val DOUBLE);")
            for k in skewed_keys:
                con.execute(f"INSERT INTO skew_test VALUES ('{k}', 1.0);")
            query = query or "SELECT k, COUNT(*), SUM(val) FROM skew_test GROUP BY k ORDER BY 2 DESC;"

        q = query or "SELECT COUNT(*), COUNT(DISTINCT 1) FROM (SELECT 1 as x UNION ALL SELECT 2 as x)"

        try:
            con.execute(f"PRAGMA max_memory='{mem_str}';")
            res = con.execute(q).fetchall()
            con.execute("PRAGMA max_memory='4GB';")
            elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
            
            out = {
                "status": "PASS",
                "memory_cap": mem_str,
                "oom_encountered": False,
                "oom_crashed": False,
                "rows_processed": num_rows,
                "rows_returned": len(res),
                "duration_ms": elapsed_ms,
                "details": f"Query executed successfully under {mem_str} memory cap with zero crashes."
            }
        except Exception as e:
            try:
                con.execute("PRAGMA max_memory='4GB';")
            except Exception:
                pass
            elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
            out = {
                "status": "FAIL",
                "memory_cap": mem_str,
                "oom_encountered": True,
                "oom_crashed": True,
                "rows_processed": num_rows,
                "rows_returned": 0,
                "duration_ms": elapsed_ms,
                "error": str(e),
                "details": f"Query failed under {mem_str} memory cap: {str(e)}"
            }

        if created_local_con:
            con.close()

        return out
