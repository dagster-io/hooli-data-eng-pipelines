from hooli_data_eng import hooli_data_eng


def test_repo_can_load():
    assert hooli_data_eng.get_job("everything_everywhere_job")
    assert hooli_data_eng.get_job("refresh_forecast_model_job")
