import re
from math import floor


FILLER_WORDS = {
    "um",
    "uh",
    "like",
    "basically",
    "actually",
    "literally",
    "you know",
}

STAR_SIGNALS = {
    "situation": ["situation", "context", "background", "problem"],
    "task": ["task", "goal", "responsibility", "objective"],
    "action": ["action", "built", "created", "implemented", "improved", "designed", "solved"],
    "result": ["result", "impact", "outcome", "reduced", "increased", "improved", "learned"],
}


def normalize_words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9']+", text.lower())



def keyword_coverage(question_data: dict, answer: str) -> tuple[int, list[str]]:
    keywords = question_data.get("keywords", [])
    normalized_answer = " ".join(normalize_words(answer))
    matched = []

    for keyword in keywords:
        keyword_parts = normalize_words(keyword)
        if keyword_parts and all(part in normalized_answer for part in keyword_parts):
            matched.append(keyword)

    if not keywords:
        return 100, matched

    score = round((len(matched) / len(keywords)) * 100)
    return score, matched



def score_structure(answer: str) -> int:
    lowered = answer.lower()
    sections_hit = 0
    for words in STAR_SIGNALS.values():
        if any(word in lowered for word in words):
            sections_hit += 1

    return round((sections_hit / len(STAR_SIGNALS)) * 100)



def score_clarity(answer: str) -> int:
    words = normalize_words(answer)
    word_count = len(words)
    sentence_count = max(1, len(re.findall(r"[.!?]", answer)))

    if word_count < 40:
        length_score = 40
    elif word_count < 80:
        length_score = 65
    elif word_count <= 220:
        length_score = 90
    else:
        length_score = 70

    sentence_score = 90 if sentence_count >= 3 else 60
    return round((length_score + sentence_score) / 2)



def score_technical_accuracy(question_data: dict, answer: str) -> int:
    """Score technical accuracy based on category-specific criteria."""
    category = question_data.get("category", "")
    lowered = answer.lower()

    if category == "Cybersecurity":
        # Check for cybersecurity-specific concepts
        security_terms = ["confidentiality", "integrity", "availability", "encryption", "authentication",
                         "firewall", "vulnerability", "threat", "risk", "compliance"]
        term_count = sum(1 for term in security_terms if term in lowered)
        accuracy_score = min(100, term_count * 15)  # Max 100 with 6+ terms
        return max(40, accuracy_score)

    elif category in ["DSA", "System Design"]:
        # Check for technical terms and concepts
        tech_indicators = ["algorithm", "complexity", "time", "space", "optimization", "design",
                          "architecture", "scalability", "performance", "efficiency"]
        indicator_count = sum(1 for indicator in tech_indicators if indicator in lowered)
        accuracy_score = min(100, indicator_count * 12)  # Max 100 with 8+ indicators
        return max(35, accuracy_score)

    elif category == "DBMS":
        # Check for database concepts
        db_terms = ["query", "table", "index", "join", "normalization", "transaction",
                   "acid", "primary key", "foreign key", "sql"]
        term_count = sum(1 for term in db_terms if term in lowered)
        accuracy_score = min(100, term_count * 15)
        return max(40, accuracy_score)

    elif category == "Operating Systems":
        # Check for OS concepts
        os_terms = ["process", "thread", "memory", "cpu", "scheduling", "deadlock",
                   "virtual memory", "paging", "kernel", "system call"]
        term_count = sum(1 for term in os_terms if term in lowered)
        accuracy_score = min(100, term_count * 12)
        return max(35, accuracy_score)

    else:
        # For HR, Projects, and other categories, base on keyword coverage
        relevance_score, _ = keyword_coverage(question_data, answer)
        return relevance_score


def score_completeness(answer: str) -> int:
    """Score answer completeness based on content depth."""
    words = normalize_words(answer)
    word_count = len(words)

    # Check for different aspects of a complete answer
    has_examples = any(word in answer.lower() for word in ["example", "for instance", "such as", "like"])
    has_metrics = any(char.isdigit() for char in answer) or any(word in answer.lower() for word in ["percent", "improved", "increased", "reduced"])
    has_impact = any(word in answer.lower() for word in ["impact", "result", "outcome", "achieved", "learned"])

    completeness_factors = sum([has_examples, has_metrics, has_impact])

    # Base score on length and completeness factors
    if word_count < 50:
        base_score = 50
    elif word_count < 100:
        base_score = 70
    elif word_count < 150:
        base_score = 85
    else:
        base_score = 95

    # Bonus for completeness
    bonus = completeness_factors * 8
    return min(100, base_score + bonus)


def score_specificity(answer: str) -> int:
    """Score how specific and detailed the answer is."""
    words = normalize_words(answer)

    # Check for vague vs specific language
    vague_words = ["thing", "stuff", "something", "things", "good", "bad", "nice", "okay"]
    specific_indicators = ["specific", "particular", "exact", "precise", "detailed"]

    vague_count = sum(1 for word in words if word in vague_words)
    specific_count = sum(1 for word in words if word in specific_indicators)

    # Penalize vague language, reward specific language
    specificity_score = 100 - (vague_count * 10) + (specific_count * 15)
    return max(30, min(100, specificity_score))



def score_confidence(answer: str) -> int:
    lowered = answer.lower()
    words = normalize_words(answer)
    word_count = max(1, len(words))
    filler_hits = sum(lowered.count(word) for word in FILLER_WORDS)
    filler_ratio = filler_hits / word_count

    score = 100 - floor(filler_ratio * 300)
    return max(45, min(100, score))



def build_strengths(result: dict) -> list[str]:
    strengths = []
    if result["relevance_score"] >= 70:
        strengths.append("You covered many of the points interviewers typically expect in this answer.")
    if result["structure_score"] >= 75:
        strengths.append("Your answer shows a clear structure, which makes it easier to follow in an interview.")
    if result["clarity_score"] >= 75:
        strengths.append("The answer length is balanced and detailed enough to sound thoughtful.")
    if result["confidence_score"] >= 80:
        strengths.append("The language feels confident with limited filler words.")
    if result.get("technical_accuracy_score", 0) >= 70:
        strengths.append("You demonstrated good technical knowledge and accuracy in your response.")
    if result.get("completeness_score", 0) >= 75:
        strengths.append("Your answer is comprehensive with examples and measurable outcomes.")
    if result.get("specificity_score", 0) >= 75:
        strengths.append("You provided specific details rather than vague generalizations.")

    if not strengths:
        strengths.append("You have a starting point to build from, and a little more detail can quickly improve this answer.")
    return strengths



def build_improvements(question_data: dict, result: dict, matched_keywords: list[str], answer: str) -> list[str]:
    improvements = []
    missing_keywords = [item for item in question_data.get("keywords", []) if item not in matched_keywords]

    if missing_keywords:
        improvements.append("Add these important points: " + ", ".join(missing_keywords[:4]) + ".")
    if result["structure_score"] < 75:
        improvements.append("Use a stronger flow like Situation, Task, Action, and Result to make the answer more interview-ready.")
    if result["clarity_score"] < 75:
        improvements.append("Add one short example and one measurable result so your answer feels more complete.")
    if result["confidence_score"] < 75:
        improvements.append("Reduce filler words and use more direct phrases such as 'I built', 'I improved', or 'I solved'.")
    if len(normalize_words(answer)) < 60:
        improvements.append("Your answer is a bit short. Expand it with context, your actions, and the final outcome.")

    # New improvement suggestions based on additional criteria
    if result.get("technical_accuracy_score", 100) < 70:
        category = question_data.get("category", "")
        if category == "Cybersecurity":
            improvements.append("Include more cybersecurity concepts like confidentiality, integrity, availability, or specific security controls.")
        elif category in ["DSA", "System Design"]:
            improvements.append("Discuss technical details like algorithms, complexity analysis, or architectural decisions.")
        elif category == "DBMS":
            improvements.append("Mention database concepts such as normalization, indexing, transactions, or query optimization.")
        elif category == "Operating Systems":
            improvements.append("Cover OS fundamentals like processes, memory management, scheduling, or concurrency.")

    if result.get("completeness_score", 100) < 75:
        improvements.append("Add concrete examples, metrics, or outcomes to make your answer more compelling.")

    if result.get("specificity_score", 100) < 75:
        improvements.append("Replace vague terms with specific details. Instead of 'good results', say 'improved performance by 40%'.")

    if not improvements:
        improvements.append("This answer is strong. Focus next on practicing delivery, pacing, and eye contact.")
    return improvements



def suggest_flow(question_data: dict) -> str:
    hint = question_data.get("hint", "")
    return (
        "Start with a brief context, explain your approach, highlight the tools or decisions you used, "
        "and finish with a clear result or lesson learned. "
        f"For this question, emphasize: {hint}"
    )


def generate_category_suggestions(question_data: dict, result: dict) -> list[str]:
    """Generate category-specific suggestions for improvement."""
    category = question_data.get("category", "")
    suggestions = []

    if category == "Cybersecurity":
        suggestions.append("🔒 **Security Best Practice**: Always mention the CIA triad (Confidentiality, Integrity, Availability) when discussing security fundamentals.")
        suggestions.append("🛡️ **Practical Examples**: Include real-world examples like 'SQL injection can be prevented by using prepared statements'.")
        suggestions.append("📋 **Compliance Angle**: Consider mentioning relevant standards like GDPR, HIPAA, or ISO 27001 when applicable.")
        if result.get("technical_accuracy_score", 0) < 70:
            suggestions.append("🎯 **Key Terms**: Incorporate terms like 'encryption', 'authentication', 'threat modeling', or 'risk assessment'.")

    elif category == "DSA":
        suggestions.append("⚡ **Complexity Analysis**: Always mention time and space complexity - O(n), O(log n), etc.")
        suggestions.append("🔄 **Trade-offs**: Discuss when to use different data structures and their trade-offs.")
        suggestions.append("💡 **Optimization**: Explain how you would optimize from brute force to efficient solutions.")
        if result.get("technical_accuracy_score", 0) < 70:
            suggestions.append("📊 **Algorithm Types**: Cover concepts like greedy algorithms, dynamic programming, or graph traversal.")

    elif category == "System Design":
        suggestions.append("🏗️ **Scalability**: Discuss how your design handles growth - horizontal/vertical scaling, load balancing.")
        suggestions.append("💾 **Data Storage**: Explain database choices, caching strategies, and data partitioning.")
        suggestions.append("🔄 **Trade-offs**: Mention CAP theorem, consistency vs availability decisions.")
        if result.get("technical_accuracy_score", 0) < 70:
            suggestions.append("🌐 **Architecture**: Cover microservices, APIs, message queues, and distributed systems.")

    elif category == "DBMS":
        suggestions.append("🔑 **Keys & Relationships**: Explain primary keys, foreign keys, and normalization forms.")
        suggestions.append("⚡ **Performance**: Discuss indexing, query optimization, and execution plans.")
        suggestions.append("🔒 **ACID Properties**: Cover Atomicity, Consistency, Isolation, Durability for transactions.")
        if result.get("technical_accuracy_score", 0) < 70:
            suggestions.append("📊 **SQL Concepts**: Include JOIN types, subqueries, stored procedures, and database design.")

    elif category == "Operating Systems":
        suggestions.append("🔄 **Concurrency**: Explain processes vs threads, synchronization, and deadlock prevention.")
        suggestions.append("💾 **Memory Management**: Cover virtual memory, paging, segmentation, and memory allocation.")
        suggestions.append("⚡ **Scheduling**: Discuss CPU scheduling algorithms and their characteristics.")
        if result.get("technical_accuracy_score", 0) < 70:
            suggestions.append("🖥️ **OS Components**: Include file systems, I/O management, and system calls.")

    elif category == "HR":
        suggestions.append("🎯 **STAR Method**: Use Situation, Task, Action, Result structure for behavioral questions.")
        suggestions.append("📈 **Quantify Impact**: Include metrics and measurable outcomes in your examples.")
        suggestions.append("🤝 **Soft Skills**: Highlight communication, leadership, and teamwork abilities.")

    elif category == "Projects":
        suggestions.append("🛠️ **Tech Stack**: Mention specific technologies, frameworks, and tools you used.")
        suggestions.append("🚀 **Challenges**: Discuss problems you faced and how you overcame them.")
        suggestions.append("📊 **Results**: Quantify the impact - users served, performance improvements, etc.")

    return suggestions[:3]  # Return top 3 suggestions



def evaluate_answer(question_data: dict, answer: str) -> dict:
    relevance_score, matched_keywords = keyword_coverage(question_data, answer)
    structure_score = score_structure(answer)
    clarity_score = score_clarity(answer)
    confidence_score = score_confidence(answer)
    technical_accuracy_score = score_technical_accuracy(question_data, answer)
    completeness_score = score_completeness(answer)
    specificity_score = score_specificity(answer)

    # Updated overall score calculation with new criteria
    overall_score = round(
        (relevance_score * 0.25)          # Reduced weight
        + (structure_score * 0.20)
        + (clarity_score * 0.15)
        + (confidence_score * 0.10)
        + (technical_accuracy_score * 0.15)  # New criterion
        + (completeness_score * 0.10)        # New criterion
        + (specificity_score * 0.05)         # New criterion
    )

    result = {
        "overall_score": overall_score,
        "relevance_score": relevance_score,
        "structure_score": structure_score,
        "clarity_score": clarity_score,
        "confidence_score": confidence_score,
        "technical_accuracy_score": technical_accuracy_score,
        "completeness_score": completeness_score,
        "specificity_score": specificity_score,
        "keyword_coverage_text": f"{len(matched_keywords)}/{len(question_data.get('keywords', []))}",
    }

    result["strengths"] = build_strengths(result)
    result["improvements"] = build_improvements(question_data, result, matched_keywords, answer)
    result["suggested_flow"] = suggest_flow(question_data)
    result["category_suggestions"] = generate_category_suggestions(question_data, result)
    return result
