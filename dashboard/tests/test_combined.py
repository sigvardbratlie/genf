import pytest
import pandas as pd
from unittest.mock import patch, Mock
import os
from dashboard.components.database_module import CombinedModule


def test_load_all_registrations():
    from .fixtures.data_buk_cash import combined_data
    from .fixtures.data_genf import registrations

    with patch("dashboard.components.database_module.get_supabase_api") as mock_get_api, \
         patch("dashboard.components.database_module.get_supabase_module") as mock_get_sm:


        mock_api = Mock()   
        mock_get_api.return_value = mock_api    
        mock_api.build_combined.return_value = pd.DataFrame(combined_data)

        mock_sm = Mock()
        mock_get_sm.return_value = mock_sm
        mock_sm.run_query.side_effect = [     
            pd.DataFrame(registrations),            
            {"some": "rates data"}      
        ]
        combined_module = CombinedModule()
        df = combined_module.load_all_registrations()

        assert isinstance(df, pd.DataFrame)
        assert "cost" in df.columns


@pytest.mark.integration
def test_load_all_registrations_integration():
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file
    with patch("dashboard.components.database_module.st") as mock_st:
        # Define mock secrets to avoid TypeError in create_client
        
        mock_st.secrets = {
            "supabase": {
                "buk_cash": {
                    "SUPABASE_URL": os.getenv("SUPABASE_URL"),
                    "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY"),
                    "API_KEY": os.getenv("API_KEY")
                },
                "genf" : {"SUPABASE_URL": os.getenv("GENF_SUPABASE_URL"),
                          "SUPABASE_ANON_KEY": os.getenv("GENF_SUPABASE_ANON_KEY")}
            }
        }
        # Fix: Mock st.session_state.get() properly with side_effect to handle different keys
        def mock_get(key, default=None):
            return {"season": "25/26"}.get(key, default)
        
        mock_st.session_state.get = Mock(side_effect=mock_get)
        print("Testing with mocked secrets:", mock_st.secrets)
        combined_module = CombinedModule()
        df = combined_module.load_all_registrations()
        assert isinstance(df, pd.DataFrame)
        assert "cost" in df.columns