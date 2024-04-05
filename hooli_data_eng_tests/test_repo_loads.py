from hooli_data_eng import hooli_data_eng


def test_repo_can_load():
    assert hooli_data_eng.get_job("refresh_analytics_model_job")
