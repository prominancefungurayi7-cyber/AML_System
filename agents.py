"""
agents.py — Agent Management Module

This module handles agent-related operations for the AML system including:
- Agent creation and validation
- Agent retrieval by code or ID
- Agent status management
- Agent transaction history queries

Functions:
    - create_agent: Create a new agent record
    - get_agent_by_code: Retrieve agent by agent code
    - get_agent_by_id: Retrieve agent by ID
    - get_all_agents: Retrieve all agents with pagination
    - get_agents_by_region: Retrieve agents by region
    - get_agents_by_city: Retrieve agents by city
    - update_agent_status: Update agent status
    - get_agent_transaction_count: Get transaction count for an agent
    - get_agent_transactions: Get transactions processed by an agent
"""

from utils import get_last_insert_id


def create_agent(conn, agent_code, agent_name, location=None, region=None, city=None, status='active'):
    """
    Create a new agent record.
    
    Args:
        conn: Database connection
        agent_code: Unique agent code
        agent_name: Agent name
        location: Agent location (optional)
        region: Agent region (optional)
        city: Agent city (optional)
        status: Agent status (default: 'active')
    
    Returns:
        Agent ID if successful, None otherwise
    """
    conn.execute(
        """
        INSERT INTO agents (agent_code, agent_name, location, region, city, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (agent_code, agent_name, location, region, city, status)
    )
    
    return get_last_insert_id(conn)


def get_agent_by_code(conn, agent_code):
    """
    Retrieve agent by agent code.
    
    Args:
        conn: Database connection
        agent_code: Agent code
    
    Returns:
        Agent row or None
    """
    return conn.execute(
        "SELECT * FROM agents WHERE agent_code=?",
        (agent_code,)
    ).fetchone()


def get_agent_by_id(conn, agent_id):
    """
    Retrieve agent by ID.
    
    Args:
        conn: Database connection
        agent_id: Agent ID
    
    Returns:
        Agent row or None
    """
    return conn.execute(
        "SELECT * FROM agents WHERE id=?",
        (agent_id,)
    ).fetchone()


def get_all_agents(conn, limit=100, offset=0):
    """
    Retrieve all agents with pagination.
    
    Args:
        conn: Database connection
        limit: Maximum number of agents to return
        offset: Number of agents to skip
    
    Returns:
        List of agent rows
    """
    return conn.execute(
        "SELECT * FROM agents ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset)
    ).fetchall()


def get_agents_by_region(conn, region, limit=100):
    """
    Retrieve agents by region.
    
    Args:
        conn: Database connection
        region: Region to filter by
        limit: Maximum number of agents to return
    
    Returns:
        List of agent rows
    """
    return conn.execute(
        "SELECT * FROM agents WHERE region=? ORDER BY created_at DESC LIMIT ?",
        (region, limit)
    ).fetchall()


def get_agents_by_city(conn, city, limit=100):
    """
    Retrieve agents by city.
    
    Args:
        conn: Database connection
        city: City to filter by
        limit: Maximum number of agents to return
    
    Returns:
        List of agent rows
    """
    return conn.execute(
        "SELECT * FROM agents WHERE city=? ORDER BY created_at DESC LIMIT ?",
        (city, limit)
    ).fetchall()


def update_agent_status(conn, agent_id, status):
    """
    Update agent status.
    
    Args:
        conn: Database connection
        agent_id: Agent ID
        status: New status
    """
    conn.execute(
        "UPDATE agents SET status=? WHERE id=?",
        (status, agent_id)
    )


def get_agent_transaction_count(conn, agent_id):
    """
    Get the total number of transactions processed by an agent.
    
    Args:
        conn: Database connection
        agent_id: Agent ID
    
    Returns:
        Transaction count
    """
    result = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE agent_id=?",
        (agent_id,)
    ).fetchone()
    return result[0] if result else 0


def get_agent_transactions(conn, agent_id, limit=50):
    """
    Retrieve transactions processed by an agent.
    
    Args:
        conn: Database connection
        agent_id: Agent ID
        limit: Maximum number of transactions to return
    
    Returns:
        List of transaction rows
    """
    return conn.execute(
        "SELECT * FROM transactions WHERE agent_id=? ORDER BY timestamp DESC LIMIT ?",
        (agent_id, limit)
    ).fetchall()


def get_agent_wallets(conn, agent_id, limit=100):
    """
    Retrieve wallets that have used an agent.
    
    Args:
        conn: Database connection
        agent_id: Agent ID
        limit: Maximum number of wallets to return
    
    Returns:
        List of unique wallet account numbers
    """
    return conn.execute(
        """
        SELECT DISTINCT sender_account as account_number FROM transactions WHERE agent_id=?
        UNION
        SELECT DISTINCT receiver_account as account_number FROM transactions WHERE agent_id=?
        LIMIT ?
        """,
        (agent_id, agent_id, limit)
    ).fetchall()


def get_agent_statistics(conn, agent_id):
    """
    Get statistics for an agent.
    
    Args:
        conn: Database connection
        agent_id: Agent ID
    
    Returns:
        Dictionary with agent statistics
    """
    total_txns = get_agent_transaction_count(conn, agent_id)
    
    total_amount = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE agent_id=?",
        (agent_id,)
    ).fetchone()[0]
    
    unique_wallets = conn.execute(
        """
        SELECT COUNT(DISTINCT sender_account) + COUNT(DISTINCT receiver_account)
        FROM transactions WHERE agent_id=?
        """,
        (agent_id,)
    ).fetchone()[0]
    
    return {
        'total_transactions': total_txns,
        'total_amount': float(total_amount) if total_amount else 0.0,
        'unique_wallets': unique_wallets if unique_wallets else 0
    }
