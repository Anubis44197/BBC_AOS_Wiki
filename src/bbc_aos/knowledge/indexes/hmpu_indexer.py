"""
BBC HMPU Indexer - Phase 4
Implements 128-bit SimHash (SHA-256) document indexing, Hamming distance
calculations, hybrid vector search, and BBCScalar aura-weighted integrations.
"""

import json
import time
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Import components from core scalar layer
from bbc_aos.core.bbc_scalar import BBCScalar, STABLE, WEAK, SLEEPING, DEGENERATE, BBCEncoder

# Set up logging namespace
logger = logging.getLogger("bbc_aos.knowledge.indexes.hmpu_indexer")


def compute_simhash(text: str) -> int:
    """
    Computes a 128-bit SimHash fingerprint of the given text using SHA-256.

    Args:
        text: Input string content.

    Returns:
        The 128-bit fingerprint as an integer.
    """
    features: Dict[str, int] = {}
    words = text.lower().split()
    for w in words:
        features[w] = features.get(w, 0) + 1

    v = [0] * 128

    for word, weight in features.items():
        h = int(hashlib.sha256(word.encode('utf-8')).hexdigest()[:32], 16)
        for i in range(128):
            bit_mask = 1 << i
            if h & bit_mask:
                v[i] += weight
            else:
                v[i] -= weight

    fingerprint = 0
    for i in range(128):
        if v[i] > 0:
            fingerprint |= (1 << i)

    return fingerprint


def hamming_distance(hash1: int, hash2: int) -> int:
    """
    Computes the Hamming distance between two 128-bit SimHash values.

    Args:
        hash1: First fingerprint.
        hash2: Second fingerprint.

    Returns:
        Hamming distance integer (0 to 128).
    """
    xor = hash1 ^ hash2
    distance = 0
    while xor:
        distance += xor & 1
        xor >>= 1
    return distance


def similarity_score(hash1: int, hash2: int) -> float:
    """
    Computes the percentage similarity (0-100) between two fingerprints.

    Args:
        hash1: First fingerprint.
        hash2: Second fingerprint.

    Returns:
        Similarity score float between 0.0 and 100.0.
    """
    dist = hamming_distance(hash1, hash2)
    return max(0.0, 100.0 - (dist / 128.0 * 100.0))


class HMPUIndexer:
    """
    HMPUIndexer manages a local database of vectorized code structures,
    facilitating structural similarity indexing and hybrid metadata searches.
    """
    
    def __init__(self, index_dir: Union[str, Path] = "02_Indices") -> None:
        """
        Initializes HMPUIndexer.

        Args:
            index_dir: Target directory path for index files.
        """
        if isinstance(index_dir, str):
            index_dir = Path(index_dir)
        self.index_dir: Path = index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.vector_db: List[Dict[str, Any]] = []
        self.is_trained: bool = True
        self.index_type: str = "PURE_BINARY_128"
        self.cache: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = {}
        logger.info(f"HMPUIndexer initialized. Storage location: '{self.index_dir}'")

    def compute_bbc_simhash(self, text: str, aura_vector: Optional[List[Any]] = None) -> BBCScalar:
        """
        Calculates a confidence score based on the Aura vector and SimHash metadata.

        Args:
            text: Document body string.
            aura_vector: Array containing [S, C, P] confidence values.

        Returns:
            A BBCScalar holding similarity quality metrics.
        """
        score = 1.0
        state = STABLE
        features: Dict[str, int] = {}
        words = text.lower().split()
        for w in words:
            features[w] = features.get(w, 0) + 1

        v = [0.0] * 128
        S, C, P = 1.0, 0.0, 0.0
        S_state = STABLE

        if aura_vector:
            try:
                S = float(aura_vector[0]) if len(aura_vector) > 0 else 1.0
                C = float(aura_vector[1]) if len(aura_vector) > 1 else 0.0
                P = float(aura_vector[2]) if len(aura_vector) > 2 else 0.0
                if hasattr(aura_vector[0], 'state'):
                    S_state = aura_vector[0].state
            except Exception as e:
                logger.warning(f"Error parsing aura vector elements: {e}")

        total_weight = 0.0
        for word, freq in features.items():
            h = int(hashlib.sha256(word.encode('utf-8')).hexdigest()[:32], 16)
            weight = freq * 1.0
            if len(word) > 5:
                weight *= (1.0 + (S * 0.2))
            if len(word) < 4:
                weight *= (1.0 - (C * 0.3))
            total_weight += weight
            for i in range(128):
                bit_mask = 1 << i
                if h & bit_mask:
                    v[i] += weight
                else:
                    v[i] -= weight

        fingerprint = 0
        for i in range(128):
            if v[i] > 0:
                fingerprint |= (1 << i)

        if S_state == DEGENERATE:
            score = 0.0
            state = DEGENERATE
        elif len(words) > 0:
            avg_weight = total_weight / len(words)
            score = min(avg_weight, 2.0) / 2.0
            if avg_weight < 0.5:
                state = WEAK
        else:
            score = 0.0
            state = SLEEPING

        return BBCScalar(score, state, metadata={"simhash": str(fingerprint), "reason": "calculated", "decay": 0.0})

    def add_to_index(self, content: str, meta: Dict[str, Any], aura_vector: Optional[List[Any]] = None) -> bool:
        """
        Adds a document using the legacy metadata-weighted API.

        Args:
            content: Document content.
            meta: Document metadata.
            aura_vector: Optional aura weighting array.

        Returns:
            True if added successfully, False otherwise.
        """
        try:
            if aura_vector:
                bbc_scalar = self.compute_bbc_simhash(content, aura_vector)
                vector_int = int(bbc_scalar.metadata.get("simhash", "0"))
                meta["method"] = "bbc_weighted"
                meta["confidence"] = bbc_scalar.value
                meta["state"] = bbc_scalar.state
                meta["simhash"] = bbc_scalar.metadata.get("simhash", "0")
            else:
                vector_int = compute_simhash(content)
                meta["method"] = "classic"

            self.vector_db.append({
                "id": meta.get("path", meta.get("id", f"doc_{len(self.vector_db)}")),
                "hash": vector_int,
                "v": str(vector_int),
                "metadata": meta,
                "timestamp": time.time()
            })
            self.cache.clear()
            return True
        except Exception as e:
            logger.error(f"Indexer error during document ingestion: {e}")
            return False

    def add_document(self, doc_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Adds a document using the standardized API.

        Args:
            doc_id: Unique identifier for the document.
            content: Document body text.
            metadata: Custom metadata dictionary.
        """
        hash_val = compute_simhash(content)
        entry = {
            "id": doc_id,
            "hash": hash_val,
            "v": str(hash_val),
            "metadata": metadata or {},
            "timestamp": time.time()
        }
        self.vector_db.append(entry)
        self.cache.clear()
        logger.debug(f"Document '{doc_id}' added to index (SimHash: {hash_val})")

    def search_similar(self, query_content: str, top_k: int = 5, threshold: float = 70.0) -> List[Dict[str, Any]]:
        """
        Executes a hybrid search combining SimHash structural score (60%) and keyword overlap (40%).

        Args:
            query_content: The search query text.
            top_k: Maximum results to return.
            threshold: Minimum hybrid score cutoff.

        Returns:
            A list of ranked result dictionaries.
        """
        query_hash = compute_simhash(query_content)
        query_words = set(query_content.lower().split())

        cache_key = (query_hash, hash(tuple(sorted(list(query_words)))), top_k, threshold)
        if cache_key in self.cache:
            return self.cache[cache_key]

        results = []
        for entry in self.vector_db:
            doc_hash = entry.get("hash", int(entry.get("v", "0")))
            simhash_score = similarity_score(query_hash, doc_hash)

            doc_words = set(entry.get("metadata", {}).get("content_summary", "").lower().split())
            if not doc_words and "id" in entry:
                doc_words = set(entry["id"].lower().replace("_", " ").split())

            overlap = query_words.intersection(doc_words)
            keyword_score = (len(overlap) / len(query_words) * 100.0) if query_words else 0.0
            hybrid_score = (simhash_score * 0.6) + (keyword_score * 0.4)

            if hybrid_score >= threshold:
                results.append({
                    "id": entry.get("id", "unknown"),
                    "similarity": hybrid_score,
                    "simhash_score": simhash_score,
                    "keyword_score": keyword_score,
                    "metadata": entry.get("metadata", {})
                })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:top_k]

        self.cache[cache_key] = results
        return results

    def search(self, query: Union[str, int], k: int = 3) -> List[Any]:
        """
        Fallback search supporting query strings or direct integer hashes.

        Args:
            query: Query string or 128-bit integer hash.
            k: Result limit.

        Returns:
            List of matching records.
        """
        if isinstance(query, str):
            return self.search_similar(query, top_k=k)

        q_vec = query
        results = []
        for item in self.vector_db:
            doc_vec = item.get("hash", int(item.get("v", "0")))
            dist = bin(q_vec ^ doc_vec).count('1')
            results.append((dist, item.get("metadata", item.get("m", {}))))

        results.sort(key=lambda x: x[0])
        return results[:k]

    def finalize_and_save(self, prefix: str, total_count: int = 0) -> str:
        """
        Serializes and saves the index database to disk.

        Args:
            prefix: Output file prefix name.
            total_count: Unused validation metric.

        Returns:
            The saved index file path.
        """
        base_path = self.index_dir / f"{prefix}_bbc_brain.json"

        serializable_db = []
        for entry in self.vector_db:
            entry_copy = dict(entry)
            entry_copy["v"] = str(entry_copy.get("hash", entry_copy.get("v", "0")))
            if "hash" in entry_copy:
                del entry_copy["hash"]
            serializable_db.append(entry_copy)

        data = {
            "type": self.index_type,
            "created": time.time(),
            "count": len(self.vector_db),
            "db": serializable_db
        }

        with open(str(base_path), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, cls=BBCEncoder)

        logger.info(f"Index database finalized and written to: '{base_path}' ({len(self.vector_db)} vectors)")
        return str(base_path)

    def load_index(self, filepath: str) -> None:
        """
        Loads the index database from file.

        Args:
            filepath: Path to the JSON database file.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            raw_db = data.get("db", data.get("vectors", []))
            self.vector_db = []
            for entry in raw_db:
                if "hash" not in entry and "v" in entry:
                    entry["hash"] = int(entry["v"])
                self.vector_db.append(entry)
            self.index_type = data.get("type", data.get("index_type", "PURE_BINARY_128"))
            logger.info(f"Index database loaded: '{filepath}' ({len(self.vector_db)} vectors)")

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics for the current index session."""
        return {
            "total_documents": len(self.vector_db),
            "index_type": self.index_type,
            "cache_size": len(self.cache),
            "index_dir": str(self.index_dir)
        }
