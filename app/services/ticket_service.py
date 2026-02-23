
from app.db.connection import get_db_connection
from datetime import datetime
import json
import uuid

class TicketService:
    
    @staticmethod
    def create_service_request(customer_id: int, session_id: str, issue: str, service_type: str, location_data: dict):
        conn = get_db_connection()
        if not conn: return None
        
        req_id = f"REQ-{uuid.uuid4().hex[:6].upper()}"
        try:
            cursor = conn.cursor()
            query = """INSERT INTO service_requests 
            (request_id, customer_id, session_id, issue_type, service_type, location_data, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'OPEN')"""
            
            cursor.execute(query, (
                req_id, customer_id, session_id, issue, service_type, json.dumps(location_data)
            ))
            conn.commit()
            return req_id
        except Exception as e:
            print(f"Error creating request: {e}")
            return None
        finally:
            if conn: conn.close()

    @staticmethod
    def create_escalation(customer_id: int, session_id: str, reason: str, collected_data: dict):
        conn = get_db_connection()
        if not conn: return False
        
        try:
            cursor = conn.cursor()
            query = """INSERT INTO escalations 
            (session_id, customer_id, reason, collected_data, status) 
            VALUES (%s, %s, %s, %s, 'OPEN')"""
            
            cursor.execute(query, (
                session_id, customer_id, reason, json.dumps(collected_data)
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creating escalation: {e}")
            return False
        finally:
            if conn: conn.close()

    @staticmethod
    def get_open_tickets():
        conn = get_db_connection()
        if not conn: return []
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            query_esc = """
            SELECT e.id, e.session_id, e.reason as type, e.status, e.created_at, e.collected_data,
                   c.name as customer_name, c.phone, c.vehicle_model, 'ESCALATION' as source
            FROM escalations e
            LEFT JOIN customers c ON e.customer_id = c.id
            WHERE e.status IN ('OPEN', 'IN_PROGRESS', 'DISPATCHED', 'ON_SITE', 'PENDING')
            """
            
            query_req = """
            SELECT r.id, r.session_id, r.issue_type as type, r.status, r.created_at, r.location_data as collected_data,
                   c.name as customer_name, c.phone, c.vehicle_model, 'REQUEST' as source
            FROM service_requests r
            LEFT JOIN customers c ON r.customer_id = c.id
            WHERE r.status IN ('OPEN', 'IN_PROGRESS', 'DISPATCHED', 'ON_SITE', 'PENDING')
            """
            
            query = f"({query_esc}) UNION ALL ({query_req}) ORDER BY 5 DESC"
            cursor.execute(query)
            items = cursor.fetchall()
            
            # Helper to parse JSON
            for item in items:
                if isinstance(item.get('collected_data'), str):
                    try:
                        item['collected_data'] = json.loads(item['collected_data'])
                    except: pass
                item['reason'] = item['type'] 
                
            return items
        except Exception as e:
            print(f"Error fetching tickets: {e}")
            return []
        finally:
            if conn: conn.close()

    @staticmethod
    def update_ticket_status(item_id: int, source: str, new_status: str):
        conn = get_db_connection()
        if not conn: return False
        
        table = 'service_requests' if source == 'REQUEST' else 'escalations'
        if table not in ['escalations', 'service_requests']: return False
            
        try:
            cursor = conn.cursor()
            query = f"UPDATE {table} SET status = %s WHERE id = %s"
            cursor.execute(query, (new_status, item_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating ticket: {e}")
            return False
        finally:
            if conn: conn.close()
